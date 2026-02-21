# AuraGC Visualizer

A/B testing and visualization suite for comparing Default GC vs AuraGC-enabled runtime.

## Overview

Project C provides:
- **Docker Compose** orchestration for side-by-side comparison
- **Locust** load testing scenarios (leak storm, spikes, steady state)
- **Streamlit** dashboard for real-time monitoring
- **Memray** profiling integration (optional)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local dashboard development)

### Running the Full Test Suite

```bash
# Start all services (baseline, auragc, locust, dashboard)
make test

# Or manually:
docker-compose -f infra/docker-compose.yaml up --build
```

This will:
1. Build two containers (baseline and AuraGC-enabled) with 512MB memory limits
2. Start Locust load generator
3. Launch Streamlit dashboard at http://localhost:8501

### Access Points

- **Baseline API**: http://localhost:8001
- **AuraGC API**: http://localhost:8002
- **Locust UI**: http://localhost:8089
- **Dashboard**: http://localhost:8501

### Running Individual Components

```bash
# Dashboard only
make dashboard

# Start services in background
make up

# Stop services
make down

# Clean up everything
make clean
```

## Load Testing Scenarios

The Locust file (`scripts/locustfile.py`) includes three user classes:

1. **LeakStormUser**: Creates cyclic references (memory leaks)
2. **SpikeUser**: Generates memory spikes with bursts
3. **SteadyStateUser**: Simulates steady background load

## Dashboard Features

The Streamlit dashboard displays:
- Real-time memory usage comparison
- GC event counts by strategy
- Process health status
- Memory usage charts with container limits

## Success Metrics

The visualizer succeeds when it clearly shows:
- **Baseline**: Memory climbs steadily until OOM kill
- **AuraGC**: Memory sawtooths and stabilizes below 512MB limit

## Development

### Local Dashboard Development

```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```

### Adding New Scenarios

Edit `scripts/locustfile.py` to add new user classes or modify existing ones.

## Notes

- Both containers are limited to 512MB memory to ensure PSI sensors can detect pressure
- The baseline container runs with `AURAGC_ENABLED=false`
- The AuraGC container runs with `AURAGC_ENABLED=true`
- Memray profiling requires additional setup (see `scripts/collect_profiles.sh`)
