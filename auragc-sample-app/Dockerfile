FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install auragc-core first (from parent context)
COPY auragc-core /tmp/auragc-core
RUN cd /tmp/auragc-core && pip install --no-cache-dir -e . || echo "auragc-core install failed, continuing without it"

# Copy requirements
COPY auragc-sample-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY auragc-sample-app/app ./app

# Set environment variable
ENV AURAGC_ENABLED=${AURAGC_ENABLED:-true}

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
