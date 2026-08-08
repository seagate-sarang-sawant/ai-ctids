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
- Python 3.9+ (3.10 recommended)
- Weights & Biases account (for training)

### 📦 Requirements Files

| File | Purpose | Size | Install Command |
|------|---------|------|-----------------|
| `requirements.txt` | **Complete installation** | All deps | `pip install -r requirements.txt` |
| `requirements-minimal.txt` | **Production-only** | Inference API | `pip install -r requirements-minimal.txt` |
| `requirements-dev.txt` | **Development tools** | Testing, linting | `pip install -r requirements-dev.txt` |
| `*/requirements.txt` | **Service-specific** | Individual services | `pip install -r service/requirements.txt` |

See [Requirements Guide](docs/REQUIREMENTS_GUIDE.md) for detailed information.

### Local Development Setup

**Option 1: Quick Install (Recommended)**
```bash
git clone <repository-url>
cd ai-ctids
./install.sh full  # or 'dev' for development tools, 'minimal' for production
source venv/bin/activate
```

**Option 2: Manual Setup**
```bash
# 1. Clone and create environment
git clone <repository-url>
cd ai-ctids
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt  # Full installation
# OR
pip install -r requirements-minimal.txt  # Production-only
# OR
pip install -r requirements-dev.txt  # With development tools

# 3. Using Makefile (alternative)
make setup    # Create venv and directories
make install  # Install all dependencies
```

**Start Services**
```bash
# Start infrastructure
docker-compose up -d kafka zookeeper prometheus grafana

# Train models
make train
# OR
cd batch-trainer && python train.py --data-path ../data/cicids2017.csv

# Start API server
make api-dev
# OR
cd inference-api && uvicorn main:app --reload
```

## 📊 Models & Performance Results

**Seven models** comprehensively evaluated on CICIDS2017 dataset:

### Machine Learning Models (4)
1. **Decision Tree** - 🏆 **Best Overall** (F1: 85.30%, Acc: 99.74%) - **DEPLOYED**
2. **Random Forest** - Highest Precision (85.30%, ROC-AUC: 99.96%)
3. **XGBoost** - Highest Accuracy (99.88%, ROC-AUC: 99.99%)
4. **Logistic Regression** - Baseline (F1: 27.57%)

### Deep Learning Models (3)
5. **Artificial Neural Network (ANN)** - Best DL Model (F1: 63.81%, Acc: 99.56%)
6. **LSTM** - Temporal Pattern Learning (F1: 60.39%, Acc: 98.24%)
7. **1D-CNN** - Spatial Pattern Learning (F1: 42.73%, Acc: 95.20%)

### 🏆 Selected Production Model: **Decision Tree**

**Why Decision Tree?**
- ✅ Highest F1-Score (85.30%) - Best balanced performance across all 15 attack classes
- ✅ Excellent Recall (90.98%) - Catches 91% of attacks (critical for security)
- ✅ Fastest Inference (0.09 sec) - Real-time detection capability
- ✅ Interpretable - Explainable decisions for security analysts
- ✅ Production-ready with 99.74% accuracy on unseen data

### 📊 Quick Performance Comparison

| Model | F1-Score | Accuracy | Inference Time | Category |
|-------|----------|----------|----------------|----------|
| **Decision Tree** 🏆 | **85.30%** | **99.74%** | **0.09 sec** | ML |
| Random Forest | 79.31% | 99.17% | 5.47 sec | ML |
| XGBoost | 76.28% | 99.88% | 36.71 sec | ML |
| ANN | 63.81% | 99.56% | 28.08 sec | DL |
| LSTM | 60.39% | 98.24% | 106.27 sec | DL |
| 1D-CNN | 42.73% | 95.20% | 49.55 sec | DL |
| Logistic Regression | 27.57% | 66.07% | 0.14 sec | ML |

**📚 Comprehensive Results**: See [MODEL_RESULTS.md](docs/MODEL_RESULTS.md) for:
- Complete performance metrics and analysis
- Feature importance rankings
- Model architecture details
- Computational performance benchmarks
- Explainable AI (SHAP/LIME) insights
- Attack detection performance by class
- Production deployment recommendations

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
✅ **Seven models** comprehensively evaluated: 4 ML + 3 Deep Learning
✅ **Decision Tree** selected as production model (F1: 85.30%, 99.74% accuracy)
✅ Batch and real-time inference support
✅ Comprehensive feature engineering (69 features from CICIDS2017)
✅ Explainable AI with SHAP and LIME for model interpretability

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

### Core Guides
- [Requirements Guide](docs/REQUIREMENTS_GUIDE.md) - **⭐ START HERE** - Dependency management
- [API Documentation](docs/API.md) - REST API reference with examples
- [Deployment Guide](docs/DEPLOYMENT.md) - Local, K8s, and cloud deployment
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Project Summary](docs/PROJECT_SUMMARY.md) - Complete feature list

### Development
- [Contributing](CONTRIBUTING.md) - Development guidelines
- [Pandas vs NumPy Quick Reference](docs/QUICK_REFERENCE_PANDAS_VS_NUMPY.md) - Aggregation behavior guide
- [Why .sum().sum()?](docs/PANDAS_SUM_EXPLAINED.md) - Detailed explanation with examples

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
- ✅ **Batch training pipeline with 7 models** (4 ML + 3 DL)
- ✅ **Model evaluation & comparison** with comprehensive metrics
- ✅ **Decision Tree deployed** as production model (85.30% F1-score)
- ✅ REST API for inference
- ✅ Kafka streaming consumer
- ✅ Real-time drift monitoring
- ✅ Complete observability stack (Prometheus + Grafana)
- ✅ Automated CI/CD pipeline with GitHub Actions
- ✅ Docker containerization for all services
- ✅ **Explainable AI** (SHAP + LIME) for model transparency
- ✅ Comprehensive documentation with [detailed results](docs/MODEL_RESULTS.md)

## 🤝 Contributing

See CONTRIBUTING.md for guidelines
