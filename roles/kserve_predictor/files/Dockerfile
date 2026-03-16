FROM python:3.10-slim

WORKDIR /app

# Install system dependencies required by Prophet (cmdstan)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY model.py .
COPY inference.py .

# Environment defaults (overridable via K8s env vars)
ENV PREDICTION_HORIZON_MINUTES=30
ENV CPU_HIGH_THRESHOLD=0.80
ENV CPU_LOW_THRESHOLD=0.10
ENV MEMORY_HIGH_THRESHOLD=0.85
ENV MEMORY_LOW_THRESHOLD=0.10
ENV CONFIDENCE_THRESHOLD=0.70
ENV PREDICTOR_PORT=8080
ENV LOG_LEVEL=INFO

EXPOSE 8080

ENTRYPOINT ["python", "inference.py"]
