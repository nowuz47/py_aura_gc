/* PSI Monitor - Low-latency memory pressure sensing via /proc/pressure/memory
 *
 * Uses poll() to monitor Linux Pressure Stall Information (PSI) for memory.
 * Signals when "some" or "full" pressure exceeds configured thresholds.
 */

#include "common.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define PSI_PATH "/proc/pressure/memory"
#define MAX_LINE_LEN 256

/* Parse PSI line: "some avg10=0.00 avg60=0.00 avg300=0.00 total=0" */
static int parse_psi_line(const char *line, const char *prefix, double *avg10) {
  char *found = strstr(line, prefix);
  if (!found)
    return -1;

  found = strstr(found, "avg10=");
  if (!found)
    return -1;

  return sscanf(found, "avg10=%lf", avg10);
}

/* Read current PSI pressure from /proc/pressure/memory */
int auragc_psi_read(auragc_psi_reading_t *reading) {
  FILE *fp = fopen(PSI_PATH, "r");
  if (!fp) {
    return -1;
  }

  char line[MAX_LINE_LEN];
  double some_avg10 = 0.0;
  double full_avg10 = 0.0;
  bool found_some = false;
  bool found_full = false;

  while (fgets(line, sizeof(line), fp)) {
    if (strncmp(line, "some", 4) == 0) {
      if (parse_psi_line(line, "some", &some_avg10) == 1) {
        found_some = true;
      }
    } else if (strncmp(line, "full", 4) == 0) {
      if (parse_psi_line(line, "full", &full_avg10) == 1) {
        found_full = true;
      }
    }
  }

  fclose(fp);

  if (!found_some || !found_full) {
    return -1;
  }

  reading->some_pressure =
      some_avg10 / 100.0; /* Convert percentage to 0.0-1.0 */
  reading->full_pressure = full_avg10 / 100.0;

  /* Zero-Threshold Trigger: Any detectable pressure is considered critical for
   * proactive survival */
  reading->critical = (some_avg10 > 0.0) || (full_avg10 > 0.0);

  return 0;
}

/* Check if PSI pressure exceeds threshold (non-blocking) */
int auragc_psi_check_pressure(double *pressure_out) {
  auragc_psi_reading_t reading;

  if (auragc_psi_read(&reading) != 0) {
    return -1;
  }

  *pressure_out = reading.some_pressure;

  /* Return 1 if pressure exceeds threshold, 0 otherwise */
  return (reading.some_pressure * 100.0 >= PSI_PRESSURE_THRESHOLD_MS) ? 1 : 0;
}
