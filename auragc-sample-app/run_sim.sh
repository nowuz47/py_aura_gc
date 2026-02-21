#!/bin/bash
# Run the AuraGC sample application

# Check if Python 3.14 is available
if command -v python3.14 &> /dev/null; then
    PYTHON=python3.14
elif command -v python3.13 &> /dev/null; then
    PYTHON=python3.13
elif command -v python3.12 &> /dev/null; then
    PYTHON=python3.12
else
    PYTHON=python3
fi

echo "Using Python: $PYTHON"
$PYTHON --version

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv
fi

source venv/bin/activate

# Install auragc-core (local dependency)
if [ -d "../auragc-core" ]; then
    echo "Installing auragc-core..."
    pip install -e ../auragc-core
fi

# Install app dependencies
pip install -r requirements.txt

# Run the application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
