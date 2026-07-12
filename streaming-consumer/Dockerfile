FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY streaming-consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY streaming-consumer/ .
COPY shared/ ./shared
COPY models/ ./models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose metrics port
EXPOSE 8001

# Run consumer
CMD ["python", "consumer.py"]
