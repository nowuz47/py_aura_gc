# AuraGC Sample Application

FastAPI application demonstrating AuraGC integration with Python 3.14.

## Overview

This application implements the `RuntimeInterface` for Python and provides simulation endpoints to test AuraGC's effectiveness under different memory pressure scenarios.

## Features

- **Python314Adapter**: Bridges AuraGC Core to Python's GC
- **Simulation Endpoints**: Create ephemeral, cyclic, and static allocations
- **Telemetry**: Track GC events and memory pressure
- **AuraGC Integration**: Automatic GC orchestration based on PSI/cgroup sensors

## Installation

```bash
# Install auragc-core first
cd ../auragc-core
pip install -e .

# Install app dependencies
cd ../auragc-sample-app
pip install -r requirements.txt
```

## Running

### Local Development

```bash
./run_sim.sh
```

Or manually:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### With Docker

See [auragc-visualizer](../auragc-visualizer/) for Docker Compose setup.

## API Endpoints

### `POST /allocate/ephemeral?count=10000`
Creates many short-lived objects (simulates high-frequency API objects).

### `POST /allocate/cyclic?count=1000`
Creates objects with circular references (simulates memory leaks). This is the main "leak storm" scenario.

### `POST /allocate/static?size_mb=10`
Pre-loads large lookup tables (simulates objects that should be frozen).

### `GET /stats`
Returns current heap and workload statistics (used by visualizer).

### `GET /telemetry`
Returns full telemetry data for monitoring/debugging.

### `POST /gc/manual?generation=2`
Manually trigger GC for testing.

## Environment Variables

- `AURAGC_ENABLED`: Set to `true` to enable AuraGC (default: `true`)

## Architecture

The application:
1. Initializes `Python314Adapter` on startup
2. Creates `Governor` with the adapter (if AuraGC enabled)
3. Runs Governor in a background thread that evaluates pressure every second
4. Exposes FastAPI endpoints for workload simulation

See [docs/project_b_plan.md](../docs/project_b_plan.md) for detailed architecture.
