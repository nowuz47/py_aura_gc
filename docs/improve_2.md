Based on the "Tombstone Test" results, AuraGC is currently failing to maintain a stable memory plateau and is instead crashing more frequently or at lower thresholds than the default GC. This indicates that the **feedback loop is broken**: the "Sensors" are too slow, and the "Governor" is not being aggressive enough to preempt the OS-level OOM-killer.

To turn these results into a successful demo, apply the following three-tier improvement solution.

---

### 1. Tier 1: Aggressive Sensing (Project A: `native_psi.c`)

The most likely reason for the 512MB limit being breached is **sensing latency**. In a "Leak Storm," memory fills the gap between 400MB and 512MB in milliseconds.

* **Reduce Polling Timeout:** Change your `poll()` or `epoll_wait()` timeout from the default (often 100ms or 1s) to **5ms - 10ms**.
* **Zero-Threshold Trigger:** Instead of waiting for PSI to hit a certain millisecond duration, trigger the "Pressure Event" as soon as any non-zero value is detected in the `some` or `full` fields.
* **Prioritize the Sensor Thread:** Use `pthread_setschedparam` in C to set the PSI monitoring thread to a **higher priority (SCHED_FIFO or SCHED_RR)**. This ensures the sensor isn't starved of CPU during heavy API traffic.

### 2. Tier 2: The "Emergency Brake" (Project A: `governor.py`)

The Governor is waiting too long to act. We must implement a "Hard Ceiling" that overrides all other heuristics.

* **Lower the Critical Threshold:** Move the `critical_threshold_mb` from 400MB to **300MB**. This provides a 200MB+ buffer for the GC to execute before hitting the 512MB container limit.
* **Recalculate Urgency ():** Modify the formula to favor the **Static Safety Margin ()**. If the current memory usage exceeds 300MB,  must immediately jump to **1.0**, regardless of the PSI signal.
* **Immediate Branding:** Upon any , call `adapter.freeze()` immediately following the `collect(2)`. This locks in the "survived" objects, reducing the scan time of the *next* emergency cycle.

### 3. Tier 3: Runtime Stability (Project B: `adapter.py`)

The premature drops to zero at 100MB suggest the GC hooks themselves are crashing the process.

* **Exception Shielding:** Wrap all C-API calls and `gc.collect()` triggers in a `try...except Exception` block within the adapter.
* **Atomic GC Calls:** Ensure that the `Governor` cannot trigger a second `collect()` while one is already in progress. Implement a simple **thread-safe lock (mutex)** in the adapter to prevent re-entrancy issues.
* **Pre-collection Cleanup:** Before calling `gc.collect(2)`, explicitly trigger a small `gc.collect(0)` to clear the most volatile objects first, reducing the workload for the full scan.

---

### **The Target "Success" Visual**

By implementing these changes, your Project C dashboard will transition from "Tombstones" to a **"Sawtooth Stability"** graph:

| Feature | Current Failure | Improvement Goal |
| --- | --- | --- |
| **Trigger Point** | ~500MB (Too late) | **300MB (Safe margin)** |
| **Collection Depth** | Drops to 0 (Crash) | **Drops to ~150MB (Success)** |
| **Uptime** | Constant Restarts | **Zero Restarts during the test** |

**Would you like me to provide the specific C code for the high-priority `native_psi.c` polling loop to ensure you don't miss any more pressure spikes?**