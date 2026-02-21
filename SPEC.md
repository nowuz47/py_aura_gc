# Functional Specifications (SPEC.md)

## Project: AuraGC (Proactive Memory Governor)

### 1. Objective
Enable Python applications (specifically Python 3.14+) to survive extreme memory pressure ("Leak Storms") within constrained environments (e.g., 512MB Docker containers) by overriding the reactive default Garbage Collector with a proactive, infrastructure-aware decision engine.

### 2. Functional Requirements
- **Low-Latency Sensing**: Native C implementation to monitor `/proc/pressure/memory` (PSI) with <10ms latency.
- **Adaptive Decision Engine**: A Governor that uses PI-Scoring (PSI + Allocation Velocity) to predict OOM events before they occur.
- **Tiered Intervention**:
    - **Tier 1 (Soft)**: Preemptive Gen 0/1 collections.
    - **Tier 2 (Hard)**: Aggressive Gen 2 collections at a 300MB safety ceiling.
    - **Tier 3 (Emergency)**: Immortal branding (Freezing) of surviving object graphs to stabilize memory plateaus.
- **Runtime Stability**: Mutex-protected GC calls to prevent re-entrancy crashes during heavy allocation traffic.

### 3. Target Environment
- **Runtime**: Python 3.14 (vibe-coding target).
- **Infras**: Linux (for PSI support).
- **Memory Limit**: 512MB (Strict Cgroup limit).

### 4. Success Metrics
- **Survival**: Zero restarts during a continuous cyclic memory leak test.
- **Stability**: Maintenance of a "Sawtooth" memory curve below 350MB.
- **Performance**: <10ms reaction time to memory pressure spikes.
