#!/bin/bash
# Build wheel, build images, deploy (alternative to cicd.sh)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Build wheel
"$PROJECT_ROOT/auragc-core/build_wheel.sh"

# Build Docker images
cd "$PROJECT_ROOT/auragc-visualizer/infra"

# Use docker compose if available, otherwise docker-compose
if docker compose version &> /dev/null; then
    docker compose build
    docker compose up -d
else
    docker-compose build
    docker-compose up -d
fi

echo "Build and deployment complete!"
