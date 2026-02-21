# AuraGC: High-Performance Garbage Collection Orchestrator

AuraGC is a high-performance, hexagonal, 3-tiered garbage collection orchestrator specifically designed for **Python 3.14 (Free-threading)**.

## Project Structure

This repository contains three independent projects:

### Project A: `auragc-core`
The domain layer that monitors system-level memory pressure (PSI/Cgroups) and decides when and how to collect garbage.

**Key Features:**
- Native C sensors for PSI and cgroup monitoring
- Python Governor for adaptive GC strategy selection
- RuntimeInterface port for runtime-agnostic GC control

**See:** [auragc-core/README.md](auragc-core/README.md)

### Project B: `auragc-sample-app`
FastAPI application that implements the RuntimeInterface for Python 3.14 and provides simulation endpoints.

**Key Features:**
- Python314Adapter bridging AuraGC Core to Python GC
- FastAPI endpoints for memory workload simulation
- Integration with AuraGC Governor

**See:** [auragc-sample-app/](auragc-sample-app/)

### Project C: `auragc-visualizer`
A/B testing and visualization suite for comparing Default GC vs AuraGC-enabled runtime.

**Key Features:**
- Docker Compose orchestration
- Locust load testing
- Streamlit dashboard
- Memray profiling integration

**See:** [auragc-visualizer/README.md](auragc-visualizer/README.md)

## Architecture

See [docs/architecture.md](docs/architecture.md) for the complete technical specification.

## Quick Start

### 1. Install Project A (Core)

```bash
cd auragc-core
pip install -e .
```

**Note:** Native sensors require Linux. On macOS/Windows, sensors will gracefully degrade.

### 2. Run Project B (Sample App)

```bash
cd auragc-sample-app
./run_sim.sh
```

The FastAPI app will be available at http://localhost:8000

### 3. Run Project C (Visualizer)

```bash
cd auragc-visualizer
make test
```

Access the dashboard at http://localhost:8501

## Development

Each project has its own development setup. See individual project READMEs for details.

## Documentation

- [Architecture](docs/architecture.md)
- [Project A Plan](docs/project_a_plan.md)
- [Project B Plan](docs/project_b_plan.md)
- [Project C Plan](docs/project_c_plan.md)

## License

MIT License
