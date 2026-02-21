#!/bin/bash
# Build auragc-core wheel and copy to wheels directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WHEELS_DIR="$PROJECT_ROOT/wheels"

# Create wheels directory
mkdir -p "$WHEELS_DIR"

# Build wheel
cd "$SCRIPT_DIR"
python3 setup.py bdist_wheel

# Copy wheel to wheels directory
cp dist/auragc_core-*.whl "$WHEELS_DIR/"

echo "Wheel built and copied to $WHEELS_DIR"
