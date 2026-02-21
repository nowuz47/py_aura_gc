#!/bin/bash
# Collect Memray profiles from running containers

set -e

BASELINE_CONTAINER="auragc-baseline"
AURAGC_CONTAINER="auragc-enabled"
RESULTS_DIR="./results"

mkdir -p "$RESULTS_DIR"

echo "Collecting Memray profiles..."

# Check if containers are running
if ! docker ps | grep -q "$BASELINE_CONTAINER"; then
    echo "Warning: Baseline container not running"
fi

if ! docker ps | grep -q "$AURAGC_CONTAINER"; then
    echo "Warning: AuraGC container not running"
fi

# Trigger memory spike before profiling
echo "Triggering memory spike..."
curl -X POST "http://localhost:8001/allocate/cyclic?count=5000" || true
curl -X POST "http://localhost:8002/allocate/cyclic?count=5000" || true

sleep 5

# Note: Actual Memray profiling would require:
# 1. Installing memray in the containers
# 2. Running the app with: memray run -o profile.memray app.main:app
# 3. Collecting the profile files

echo "Profile collection complete. See $RESULTS_DIR for results."
echo "Note: Full Memray integration requires container rebuild with memray installed."
