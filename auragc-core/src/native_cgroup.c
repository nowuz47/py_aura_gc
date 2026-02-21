/* Cgroup Watcher - Monitor cgroup v2 memory events
 *
 * Watches memory.events for high, max, or oom events to prevent OOM kills
 * in containerized (K8s) environments.
 */

#include "common.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define CGROUP_EVENTS_PATH "/sys/fs/cgroup/memory.events"
#define MAX_LINE_LEN 256

/* Find cgroup v2 memory.events file (may be in different locations) */
static const char *find_cgroup_events_path(void) {
  /* Try common locations */
  static const char *paths[] = {"/sys/fs/cgroup/memory.events",
                                "/sys/fs/cgroup/memory/memory.events", NULL};

  for (int i = 0; paths[i]; i++) {
    if (access(paths[i], R_OK) == 0) {
      return paths[i];
    }
  }

  return NULL;
}

/* Parse memory.events line: "high 0\n" or "max 1\n" or "oom 0\n" */
static int parse_event_count(const char *line, const char *event_name,
                             uint64_t *count) {
  size_t name_len = strlen(event_name);
  if (strncmp(line, event_name, name_len) != 0) {
    return -1;
  }

  if (line[name_len] != ' ') {
    return -1;
  }

  return sscanf(line + name_len + 1, "%lu", count);
}

/* Read cgroup memory events */
int auragc_cgroup_read_events(auragc_cgroup_memory_event_t *event) {
  const char *path = find_cgroup_events_path();
  if (!path) {
    /* Cgroup v2 not available or not in container */
    event->event_type = AURAGC_CGROUP_NONE;
    event->critical = false;
    return 0; /* Not an error, just not available */
  }

  FILE *fp = fopen(path, "r");
  if (!fp) {
    return -1;
  }

  /* Static state to track cumulative deltas */
  static uint64_t last_high_count = 0;
  static uint64_t last_max_count = 0;
  static uint64_t last_oom_count = 0;

  char line[MAX_LINE_LEN];
  uint64_t high_count = 0;
  uint64_t max_count = 0;
  uint64_t oom_count = 0;

  while (fgets(line, sizeof(line), fp)) {
    parse_event_count(line, "high", &high_count);
    parse_event_count(line, "max", &max_count);
    parse_event_count(line, "oom", &oom_count);
  }

  fclose(fp);

  /* Calculate deltas */
  uint64_t delta_oom =
      (oom_count > last_oom_count) ? (oom_count - last_oom_count) : 0;
  uint64_t delta_max =
      (max_count > last_max_count) ? (max_count - last_max_count) : 0;
  uint64_t delta_high =
      (high_count > last_high_count) ? (high_count - last_high_count) : 0;

  /* Update tracking state */
  if (oom_count > last_oom_count)
    last_oom_count = oom_count;
  if (max_count > last_max_count)
    last_max_count = max_count;
  if (high_count > last_high_count)
    last_high_count = high_count;

  /* Determine event type and criticality based on DELTAS, not cumulative totals
   */
  if (delta_oom > 0) {
    event->event_type = AURAGC_CGROUP_OOM;
    event->critical = true;
  } else if (delta_max > 0) {
    event->event_type = AURAGC_CGROUP_MAX;
    event->critical = true;
  } else if (delta_high > 0) {
    event->event_type = AURAGC_CGROUP_HIGH;
    event->critical = false; /* Warning, not critical */
  } else {
    event->event_type = AURAGC_CGROUP_NONE;
    event->critical = false;
  }

  return 0;
}

/* Check if cgroup is in critical state (non-blocking) */
int auragc_cgroup_is_critical(bool *critical_out) {
  auragc_cgroup_memory_event_t event;

  if (auragc_cgroup_read_events(&event) != 0) {
    return -1;
  }

  *critical_out = event.critical;
  return 0;
}

/* Read current memory pressure as a percentage of limit (fallback for missing
 * PSI) */
int auragc_cgroup_read_pressure(double *pressure_out) {
  FILE *fp_current = fopen("/sys/fs/cgroup/memory.current", "r");
  FILE *fp_max = fopen("/sys/fs/cgroup/memory.max", "r");

  // Also support older cgroup paths
  if (!fp_current || !fp_max) {
    if (fp_current)
      fclose(fp_current);
    if (fp_max)
      fclose(fp_max);

    fp_current = fopen("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r");
    fp_max = fopen("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r");
  }

  if (!fp_current || !fp_max) {
    if (fp_current)
      fclose(fp_current);
    if (fp_max)
      fclose(fp_max);
    return -1;
  }

  char current_str[64];
  char max_str[64];

  if (!fgets(current_str, sizeof(current_str), fp_current) ||
      !fgets(max_str, sizeof(max_str), fp_max)) {
    fclose(fp_current);
    fclose(fp_max);
    return -1;
  }

  fclose(fp_current);
  fclose(fp_max);

  uint64_t current = strtoull(current_str, NULL, 10);
  uint64_t max_limit;

  if (strncmp(max_str, "max", 3) == 0) {
    // If not limited, use a reasonable default for container limits (1GB) to
    // give relative pressure scale
    max_limit = 1024 * 1024 * 1024;
  } else {
    max_limit = strtoull(max_str, NULL, 10);
  }

  if (max_limit == 0) {
    *pressure_out = 0.0;
  } else {
    *pressure_out = (double)current / (double)max_limit;
    if (*pressure_out > 1.0)
      *pressure_out = 1.0;
  }

  return 0;
}
