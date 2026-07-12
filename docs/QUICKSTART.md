# Quick Start Guide

Get AI-CTIDS running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Python 3.10+ (for local training)
- 8GB+ RAM
- CICIDS2017 dataset (download separately)

## Step 1: Clone and Setup (1 min)

```bash
# Clone repository
git clone <repository-url>
cd ai-ctids

# Create environment file
cp .env.example .env

# Create necessary directories
mkdir -p data models logs
```

## Step 2: Get the Dataset (External)

Download CICIDS2017 dataset and place in `data/` directory:
- Save as `data/cicids2017.csv`
- Dataset source: [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html)

## Step 3: Start Infrastructure (2 min)

```bash
# Start Kafka and monitoring stack
docker-compose up -d zookeeper kafka prometheus grafana

# Wait for services to be ready
sleep 30
```

## Step 4: Train Models (Local - Optional)

If you want to train models locally:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install training dependencies
pip install -r batch-trainer/requirements.txt

# Train models (will take 10-30 minutes depending on data size)
cd batch-trainer
python train.py \
    --data-path ../data/cicids2017.csv \
    --output-dir ../models \
    --models xgboost logistic_regression

cd ..
```

**OR** use pre-trained models if available (copy to `models/` directory).

## Step 5: Start ML Services (1 min)

```bash
# Start all services
docker-compose up -d inference-api streaming-consumer drift-monitor

# Check status
docker-compose ps
```

## Step 6: Verify Everything Works

### Test Inference API

```bash
# Health check
curl http://localhost:8000/healthz

# Make a prediction (example with minimal features)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "destination_port": 80,
    "flow_duration": 1234.5,
    "total_fwd_packets": 10,
    "total_backward_packets": 8,
    "total_length_of_fwd_packets": 500,
    "total_length_of_bwd_packets": 400,
    "fwd_packet_length_max": 100,
    "fwd_packet_length_min": 20,
    "fwd_packet_length_mean": 50,
    "fwd_packet_length_std": 15.5,
    "bwd_packet_length_max": 80,
    "bwd_packet_length_min": 10,
    "bwd_packet_length_mean": 40,
    "bwd_packet_length_std": 12,
    "flow_bytes_s": 10000,
    "flow_packets_s": 100,
    "flow_iat_mean": 50,
    "flow_iat_std": 10,
    "flow_iat_max": 100,
    "flow_iat_min": 10
  }'
```

### Access Dashboards

1. **API Documentation**: http://localhost:8000/docs
2. **Grafana**: http://localhost:3000 (admin/admin)
3. **Prometheus**: http://localhost:9090

## Step 7: Ingest Sample Traffic

```bash
# Start data ingestion (in new terminal)
docker-compose up data-ingestion

# Or run locally
cd data-ingestion
python generate.py \
    --data-path ../data/cicids2017.csv \
    --mode stream \
    --rate 5 \
    --kafka-servers localhost:9092
```

## What's Running?

After completing these steps:

| Service | Port | Purpose |
|---------|------|---------|
| Inference API | 8000 | REST predictions |
| Streaming Consumer | 8001 | Real-time Kafka scoring |
| Drift Monitor | 8002 | Data drift detection |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| Kafka | 9092 | Message bus |
| Zookeeper | 2181 | Kafka coordination |

## Troubleshooting

### Kafka not connecting?
```bash
# Check Kafka is running
docker-compose ps kafka

# Check logs
docker-compose logs kafka
```

### Model not loading?
```bash
# Check model files exist
ls -lh models/

# Check API logs
docker-compose logs inference-api
```

### Services not starting?
```bash
# Check available memory
docker stats

# Check logs for specific service
docker-compose logs <service-name>
```

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs for interactive API testing
2. **View Metrics**: Import Grafana dashboard from `observability/grafana/dashboards/`
3. **Test Drift Detection**: Use `--drift` flag with data generator
4. **Run Tests**: `make test` to run the test suite
5. **Read Documentation**: See `docs/` for detailed guides

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Need Help?

- Check the [full documentation](../README.md)
- See [API reference](API.md)
- Review [deployment guide](DEPLOYMENT.md)
- Check [architecture docs](ARCHITECTURE.md)

Happy threat hunting! 🎯🔒
