FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY preprocessing-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY preprocessing-service/ .
COPY shared/ ./shared
COPY models/ ./models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose metrics port
EXPOSE 8003

# Run preprocessor
CMD ["python", "preprocessor.py"]
