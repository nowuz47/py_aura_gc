# AuraGC Deployment Guide

This guide covers the multi-container deployment workflow using wheel distribution.

## Quick Start

### One-Click Deployment

```bash
# From project root
./cicd.sh

# With cleanup (removes previous containers/volumes)
./cicd.sh --clean
```

## Deployment Architecture

The deployment process follows these steps:

1. **Build Wheel**: Compile `auragc-core` as a `.whl` file
2. **Build Images**: Create Docker images using the wheel
3. **Deploy**: Start all services with Docker Compose

## Manual Deployment Steps

### 1. Build Wheel

```bash
cd auragc-core
./build_wheel.sh
```

This creates `wheels/auragc_core-*.whl` in the project root.

### 2. Build Docker Images

```bash
cd auragc-visualizer/infra
docker-compose build
# or
docker compose build
```

### 3. Deploy Services

```bash
docker-compose up -d
# or
docker compose up -d
```

## Services

After deployment, the following services are available:

- **Baseline API**: http://localhost:8001 (Default GC, AURAGC_ENABLED=false)
- **AuraGC API**: http://localhost:8002 (AuraGC enabled, AURAGC_ENABLED=true)
- **Dashboard**: http://localhost:8501 (Streamlit visualization)
- **Locust UI**: http://localhost:8089 (Load testing interface)

## Using Makefile

```bash
cd auragc-visualizer

# Build wheel and run tests
make test

# Build wheel and start services
make up

# Stop services
make down

# Clean everything
make clean

# Build wheel only
make build-wheel
```

## Alternative Scripts

### build_and_deploy.sh

```bash
./scripts/build_and_deploy.sh
```

Simpler script that builds wheel and deploys without health checks.

## Troubleshooting

### Wheel Not Found

If Docker build fails with "wheel not found":
1. Ensure `./auragc-core/build_wheel.sh` ran successfully
2. Check that `wheels/auragc_core-*.whl` exists
3. Verify Docker build context includes the `wheels/` directory

### Port Conflicts

If ports are already in use:
- Change port mappings in `auragc-visualizer/infra/docker-compose.yaml`
- Or stop conflicting services

### Build Failures

- Ensure Docker is running
- Check Python 3.12+ is installed
- Verify `wheel` package is installed: `pip install wheel`

## CI/CD Integration

The `cicd.sh` script is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Deploy AuraGC
  run: ./cicd.sh
```

The script:
- Checks all requirements
- Builds wheel
- Builds images
- Deploys services
- Performs health checks
- Shows status

## File Structure

```
py_aura_gc/
├── cicd.sh                    # One-click deployment
├── wheels/                    # Built wheels directory
│   ├── .gitkeep
│   └── auragc_core-*.whl     # Generated wheel files
├── auragc-core/
│   └── build_wheel.sh         # Wheel build script
├── auragc-sample-app/
│   └── Dockerfile             # Uses wheel from wheels/
└── auragc-visualizer/
    └── infra/
        └── docker-compose.yaml # Multi-container setup
```

## Notes

- Wheel files are gitignored (see `.gitignore`)
- Build context is project root (`../..`) so `wheels/` is accessible
- Both `baseline` and `auragc` services use the same Dockerfile with different env vars
- The wheel includes C extensions built for Linux
