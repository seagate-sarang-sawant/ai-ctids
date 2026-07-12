FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY data-ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY data-ingestion/ .
COPY shared/ ./shared
COPY data/ ./data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run generator
CMD ["python", "generate.py", "--help"]
