/* Cgroup Watcher - Monitor cgroup v2 memory events
 *
 * Watches memory.events for high, max, or oom events to prevent OOM kills
 * in containerized (K8s) environments.
 */

#include "common.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

#define CGROUP_EVENTS_PATH "/sys/fs/cgroup/memory.events"
#define MAX_LINE_LEN 256

/* Find cgroup v2 memory.events file (may be in different locations) */
static const char* find_cgroup_events_path(void) {
    /* Try common locations */
    static const char* paths[] = {
        "/sys/fs/cgroup/memory.events",
        "/sys/fs/cgroup/memory/memory.events",
        NULL
    };
    
    for (int i = 0; paths[i]; i++) {
        if (access(paths[i], R_OK) == 0) {
            return paths[i];
        }
    }
    
    return NULL;
}

/* Parse memory.events line: "high 0\n" or "max 1\n" or "oom 0\n" */
static int parse_event_count(const char *line, const char *event_name, uint64_t *count) {
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
        return 0;  /* Not an error, just not available */
    }
    
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return -1;
    }
    
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
    
    /* Determine event type and criticality */
    if (oom_count > 0) {
        event->event_type = AURAGC_CGROUP_OOM;
        event->critical = true;
    } else if (max_count > 0) {
        event->event_type = AURAGC_CGROUP_MAX;
        event->critical = true;
    } else if (high_count > 0) {
        event->event_type = AURAGC_CGROUP_HIGH;
        event->critical = false;  /* Warning, not critical */
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
