FROM python:3.12-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the core library source and build the native C extension wheel
COPY auragc-core /app/auragc-core
RUN cd auragc-core && rm -rf dist/* && pip install build wheel setuptools && python setup.py bdist_wheel && pip install dist/*.whl --no-deps --force-reinstall

# Copy requirements
COPY auragc-sample-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY auragc-sample-app/app ./app

ENV AURAGC_ENABLED=${AURAGC_ENABLED:-true}
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
