FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY drift-monitor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY drift-monitor/ .
COPY shared/ ./shared
COPY data/ ./data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose metrics port
EXPOSE 8002

# Run monitor
CMD ["python", "monitor.py", "--help"]
