#ifndef AURAGC_COMMON_H
#define AURAGC_COMMON_H

#include <stdint.h>
#include <stdbool.h>

/* Pressure Stall Information (PSI) thresholds */
#define PSI_PRESSURE_THRESHOLD_MS 10  /* 10ms window for "some" pressure */
#define PSI_CRITICAL_THRESHOLD_MS 20  /* 20ms window for "full" pressure */

/* Cgroup event types */
typedef enum {
    AURAGC_CGROUP_NONE = 0,
    AURAGC_CGROUP_HIGH,
    AURAGC_CGROUP_MAX,
    AURAGC_CGROUP_OOM
} auragc_cgroup_event_t;

/* PSI pressure reading */
typedef struct {
    double some_pressure;   /* Pressure in the "some" window (0.0-1.0) */
    double full_pressure;    /* Pressure in the "full" window (0.0-1.0) */
    bool critical;           /* True if pressure exceeds critical threshold */
} auragc_psi_reading_t;

/* Cgroup memory event */
typedef struct {
    auragc_cgroup_event_t event_type;
    bool critical;           /* True if OOM or max threshold reached */
} auragc_cgroup_memory_event_t;

/* PSI functions */
int auragc_psi_read(auragc_psi_reading_t *reading);
int auragc_psi_check_pressure(double *pressure_out);

/* Cgroup functions */
int auragc_cgroup_read_events(auragc_cgroup_memory_event_t *event);
int auragc_cgroup_is_critical(bool *critical_out);

#endif /* AURAGC_COMMON_H */
