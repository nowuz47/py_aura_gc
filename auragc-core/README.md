# AuraGC Core

High-performance garbage collection orchestrator core for Python 3.14 (Free-threading).

## Overview

AuraGC Core is the "Intelligence Layer" that monitors system-level memory pressure (PSI/Cgroups) and decides when and how to collect garbage. It uses a hexagonal architecture with:

- **Native C sensors** for low-latency PSI and cgroup monitoring
- **Python Governor** for adaptive GC strategy selection
- **RuntimeInterface port** for runtime-agnostic GC control

## Installation

```bash
cd auragc-core
pip install -e .
```

**Note:** Native sensors require Linux. On macOS/Windows, the package will install but sensors will return `None` (graceful degradation).

## Usage

```python
from auragc.core.governor import Governor
from auragc.interfaces.runtime import RuntimeInterface

# Implement RuntimeInterface (see Project B)
class MyAdapter(RuntimeInterface):
    def get_heap_usage(self):
        return {"allocated_blocks": 1000, "gen_counts": (10, 5, 2)}
    
    def trigger_gc(self, generation):
        import gc
        return gc.collect(generation)
    
    def apply_freeze(self):
        import gc
        gc.freeze()

# Create Governor with adapter
adapter = MyAdapter()
governor = Governor(adapter)

# Periodic tick (call from your event loop)
objects_freed = governor.tick()
```

## Architecture

See [docs/architecture.md](../docs/architecture.md) and [docs/project_a_plan.md](../docs/project_a_plan.md) for detailed architecture documentation.

## Development

Build C extensions:
```bash
python setup.py build_ext --inplace
```

Run tests (when implemented):
```bash
pytest
```
