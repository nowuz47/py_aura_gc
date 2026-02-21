# Architecture Decision Record & Insights (ADR.md)

## ADR 1: Native PSI vs. Python Cgroup Polling
- **Context**: Checking memory usage via `sys.getallocatedblocks()` or `/sys/fs/cgroup` in a Python thread introduced too much latency during rapid leaks.
- **Decision**: Implemented `native_psi.c` to read Linux Pressure Stall Information directly.
- **Insight**: PSI provides a "Leading Indicator" of memory exhaustion (stall time) even when RSS hasn't yet hit the limit.

## ADR 2: PI-Scoring Governor
- **Context**: Simple thresholding caused "GC Thrashing" where the collector ran too frequently.
- **Decision**: Implemented a formula: $U = (W_p \cdot PSI) + (W_v \cdot Velocity)$.
- **Insight**: Combining the *pressure* (PSI) with the *speed of change* (Velocity) allows the governor to ignore slow leaks but react instantly to "Storms".

## ADR 3: Sawtooth Stability via Immortal Branding
- **Context**: After a full GC, surviving leaked objects are often scanned again in the next cycle, wasting CPU.
- **Decision**: Integrated `gc.freeze()` immediately after an emergency collection.
- **Insight**: By branding survivors as "Immortal," we stop scanning the "leaked" portion of the heap, focusing exclusively on new garbage. This creates the stable sawtooth pattern.

## ADR 4: Re-entrancy Mutex
- **Context**: During "Leak Storms," multiple threads or rapid governor ticks could trigger overlapping GC calls, causing SIGSEGV/Crashes.
- **Decision**: Added a `threading.Lock` in the `RuntimeAdapter`.
- **Insight**: Ensuring GC atomicity is critical when overriding default runtime behaviors at high frequencies (10ms).
