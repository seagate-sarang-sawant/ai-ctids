# AI-Driven Cyber Threat Detection and Intrusion Detection System (AI-CTIDS)

Production-ready ML pipeline for detecting cyber threats using CICIDS2017 dataset.

## 🏗️ Architecture

```
ai-ctids/
├── shared/                    # Shared schemas and utilities
│   ├── schemas.py            # Pydantic models (NetworkFlowEvent, PredictionEvent)
│   ├── feature_engineering.py # Feature engineering from notebook
│   └── config.py             # Configuration management
├── batch-trainer/            # Model training pipeline
│   ├── train.py             # Training with W&B tracking
│   ├── evaluate.py          # Model evaluation and metrics
│   ├── requirements.txt     # Training dependencies
│   └── Dockerfile
├── inference-api/           # REST API for predictions
│   ├── main.py             # FastAPI application
│   ├── predictor.py        # Model loading and prediction
│   ├── requirements.txt
│   └── Dockerfile
├── streaming-consumer/      # Kafka consumer for real-time scoring
│   ├── consumer.py         # Kafka consumer implementation
│   ├── requirements.txt
│   └── Dockerfile
├── data-ingestion/         # Data ingestion and simulation
│   ├── generate.py        # Batch and streaming data ingestion
│   ├── requirements.txt
│   └── Dockerfile
├── drift-monitor/         # Model drift detection
│   ├── monitor.py        # PSI calculation and alerting
│   ├── requirements.txt
│   └── Dockerfile
├── observability/        # Monitoring and observability
│   ├── prometheus.yml   # Prometheus configuration
│   └── grafana/
│       └── dashboards/  # Grafana dashboard JSON
├── .github/
│   └── workflows/
│       └── train-and-publish.yml  # CI/CD pipeline
├── docker-compose.yml   # Local development stack
├── models/             # Trained model artifacts
├── data/              # Dataset storage
└── tests/            # Unit and integration tests
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Weights & Biases account (for training)

### Local Development Setup

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd ai-ctids
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start infrastructure**
```bash
docker-compose up -d kafka zookeeper prometheus grafana
```

4. **Train models**
```bash
cd batch-trainer
python train.py --data-path ../data/cicids2017.csv --wandb-project ai-ctids
```

5. **Start API server**
```bash
cd inference-api
uvicorn main:app --reload
```

## 📊 Models

Three models trained on CICIDS2017 dataset:
- **Logistic Regression** - Baseline model
- **XGBoost** - Best performing model (deployed)
- **ANN (Keras)** - Deep learning alternative

## 🔧 Tech Stack

- **Training**: scikit-learn, XGBoost, TensorFlow/Keras, Weights & Biases
- **API**: FastAPI, Pydantic, uvicorn
- **Streaming**: Apache Kafka, confluent-kafka-python
- **Monitoring**: Prometheus, Grafana, Alertmanager
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Data**: pandas, numpy, joblib

## 📡 API Endpoints

### Inference API (port 8000)

- `POST /predict` - Single or batch prediction
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `GET /metrics` - Prometheus metrics

### Example Request
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "flows": [{
      "destination_port": 80,
      "flow_duration": 1234,
      "total_fwd_packets": 10,
      ...
    }]
  }'
```

## 📈 Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

Dashboards include:
- Model performance metrics (accuracy, precision, recall)
- Inference latency and throughput
- Data quality and drift detection
- System resource utilization

## 🔄 CI/CD Pipeline

GitHub Actions workflow automatically:
1. Runs tests on pull requests
2. Trains models on push to main
3. Evaluates model performance
4. Deploys if metrics exceed thresholds
5. Supports rollback to previous version

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📝 License

MIT License - See LICENSE file for details

## 🎯 Features Delivered

### Production-Ready ML Pipeline
✅ Complete end-to-end pipeline from training to deployment
✅ Three models: Logistic Regression, XGBoost (primary), and ANN
✅ Batch and real-time inference support
✅ Comprehensive feature engineering (63 features from CICIDS2017)

### Deployment & Scalability
✅ Docker containerization for all services
✅ Kubernetes-ready configuration
✅ Horizontal scaling support
✅ Load balancer compatible
✅ Health checks and readiness probes

### MLOps Excellence
✅ Weights & Biases experiment tracking
✅ Model versioning and metadata
✅ Automated CI/CD pipeline with GitHub Actions
✅ Quality gates (accuracy and F1 thresholds)
✅ Automated rollback capability

### Monitoring & Observability
✅ Prometheus metrics collection
✅ Grafana dashboards for visualization
✅ Real-time drift detection with PSI
✅ Automated alerting
✅ Comprehensive logging

### Data Quality
✅ Input validation with Pydantic
✅ Drift injection for testing
✅ Population Stability Index monitoring
✅ Feature distribution tracking

## 📚 Documentation

- [API Documentation](docs/API.md) - REST API reference with examples
- [Deployment Guide](docs/DEPLOYMENT.md) - Local, K8s, and cloud deployment
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Project Summary](docs/PROJECT_SUMMARY.md) - Complete feature list
- [Contributing](CONTRIBUTING.md) - Development guidelines

## 🛠️ Development Commands

```bash
make help          # Show all available commands
make setup         # Initial setup
make install       # Install dependencies
make train         # Train all models
make test          # Run test suite
make lint          # Check code quality
make format        # Format code
make docker-up     # Start all services
make api-dev       # Run API in dev mode
make health-check  # Check service health
```

## 📂 Project Structure

```
ai-ctids/
├── shared/                    # Shared schemas and utilities
│   ├── schemas.py            # Pydantic models
│   ├── config.py             # Configuration
│   └── feature_engineering.py # Feature processing
├── batch-trainer/            # Training pipeline
│   ├── train.py             # Model training with W&B
│   └── evaluate.py          # Model evaluation
├── inference-api/           # REST API
│   ├── main.py             # FastAPI app
│   └── predictor.py        # Model inference
├── streaming-consumer/      # Kafka consumer
│   └── consumer.py         # Real-time scoring
├── data-ingestion/         # Data ingestion
│   └── generate.py        # Batch/stream ingestion
├── drift-monitor/         # Drift detection
│   └── monitor.py        # PSI calculation
├── observability/        # Monitoring
│   ├── prometheus.yml   # Metrics config
│   └── grafana/        # Dashboards
├── .github/workflows/  # CI/CD
│   ├── train-and-publish.yml
│   └── test.yml
├── docs/              # Documentation
├── tests/            # Test suite
└── docker-compose.yml # Local stack
```

## 🚦 System Status

All core components implemented and tested:
- ✅ Batch training pipeline with 3 models
- ✅ REST API for inference
- ✅ Kafka streaming consumer
- ✅ Real-time drift monitoring
- ✅ Complete observability stack
- ✅ Automated CI/CD pipeline
- ✅ Docker containerization
- ✅ Comprehensive documentation

## 🤝 Contributing

See CONTRIBUTING.md for guidelines
