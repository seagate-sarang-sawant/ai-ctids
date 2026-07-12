# AI-CTIDS Architecture

## System Overview

AI-CTIDS is a production-ready ML pipeline for real-time cyber threat detection using the CICIDS2017 dataset.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources (CICIDS2017)                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Ingestion                              │
│  • Batch mode: Ingest static datasets                           │
│  • Stream mode: Publish to Kafka                                │
│  • Drift injection for testing                                  │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Kafka (Message Bus)                             │
│  Topics:                                                          │
│   - network-flows (input)                                        │
│   - threat-predictions (output)                                  │
└─────┬──────────────────────────────────────────────────┬─────────┘
      │                                                   │
      │                                                   │
      ▼                                                   ▼
┌──────────────────────┐                      ┌──────────────────────┐
│  Streaming Consumer  │                      │    Drift Monitor     │
│  • Real-time scoring │                      │  • PSI calculation   │
│  • Kafka integration │                      │  • Feature tracking  │
│  • Prediction output │                      │  • Alert on drift    │
└──────────────────────┘                      └──────────────────────┘
           │                                              │
           ▼                                              ▼
┌──────────────────────┐                      ┌──────────────────────┐
│   Inference API      │                      │    Prometheus        │
│  • REST endpoints    │◄─────────────────────┤  • Metrics scraping  │
│  • Batch predictions │                      │  • Alert evaluation  │
│  • Health checks     │                      └──────────┬───────────┘
└──────────────────────┘                                 │
           │                                              ▼
           │                                   ┌──────────────────────┐
           │                                   │      Grafana         │
           │                                   │  • Dashboards        │
           └───────────────────────────────────┤  • Visualizations    │
                                               └──────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Training Pipeline                             │
│  1. Data ingestion & preprocessing                              │
│  2. Feature engineering                                          │
│  3. Model training (Logistic Regression, XGBoost, ANN)          │
│  4. Hyperparameter tuning                                        │
│  5. Model evaluation & metadata generation                       │
│  6. W&B experiment tracking                                      │
│  7. Model artifact storage                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Ingestion
**Purpose**: Ingest network flow events for testing and simulation

**Features**:
- Reads CICIDS2017 dataset
- Batch mode for static generation
- Stream mode for Kafka publishing
- Configurable event rate
- Drift injection modes:
  - `flow_duration`: Increase flow durations
  - `packet_size`: Modify packet sizes
  - `port_shift`: Change port distributions
  - `benign_to_attack`: Simulate benign → attack drift

**Technology**: Python, Pandas, confluent-kafka

### 2. Batch Training Pipeline
**Purpose**: Train and evaluate ML models

**Models**:
1. **Logistic Regression**: Baseline linear model
2. **XGBoost**: Gradient boosting (primary production model)
3. **ANN (Keras)**: Deep learning alternative

**Pipeline**:
1. Data loading and validation
2. Preprocessing (scaling, encoding)
3. Feature engineering (63 selected features)
4. Train/val/test split (70/15/15)
5. Model training with hyperparameter tuning
6. Evaluation (accuracy, precision, recall, F1, ROC-AUC)
7. Artifact serialization

**Technology**: scikit-learn, XGBoost, TensorFlow, W&B

### 3. Inference API
**Purpose**: Serve predictions via REST API

**Endpoints**:
- `POST /predict` - Single prediction
- `POST /predict/batch` - Batch predictions
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `GET /metrics` - Prometheus metrics

**Features**:
- Model loading on startup
- Feature preprocessing pipeline
- Prometheus instrumentation
- Error handling and validation

**Technology**: FastAPI, uvicorn, Pydantic

### 4. Streaming Consumer
**Purpose**: Real-time threat detection from Kafka

**Flow**:
1. Consume NetworkFlowEvent from `network-flows` topic
2. Preprocess features
3. Make prediction using loaded model
4. Publish PredictionEvent to `threat-predictions` topic

**Features**:
- Kafka consumer group for scalability
- Automatic offset management
- Graceful shutdown
- Prometheus metrics

**Technology**: confluent-kafka, Python

### 5. Drift Monitor
**Purpose**: Detect data drift in production

**Algorithm**:
- Population Stability Index (PSI)
- PSI = Σ (current% - reference%) * ln(current% / reference%)
- Threshold: PSI > 0.2 = significant drift

**Features**:
- Rolling window (configurable size)
- Per-feature PSI calculation
- Automatic alerting
- Reference distribution from training data

**Technology**: NumPy, Pandas, confluent-kafka

### 6. Observability Stack

**Prometheus**:
- Metrics collection
- Alert evaluation
- Time-series storage

**Grafana**:
- Dashboard visualization
- Alert notifications
- Multi-panel layouts

**Metrics Tracked**:
- Prediction rate and latency
- Model confidence distribution
- Drift PSI scores
- Kafka consumer lag
- Error rates

## Data Flow

### Training Flow
```
CICIDS2017 CSV
  → Data Loader
  → Preprocessor (scaling, encoding)
  → Feature Selector
  → Train/Val/Test Split
  → Model Trainer (with W&B logging)
  → Model Evaluator
  → Artifact Storage (.pkl, .keras, metadata.json)
```

### Inference Flow (API)
```
HTTP Request (NetworkFlowEvent)
  → FastAPI Handler
  → Input Validation (Pydantic)
  → Feature Preprocessing
  → Model Prediction
  → Response (PredictionEvent)
  → Metrics Update
```

### Streaming Flow
```
Kafka NetworkFlowEvent
  → Consumer Poll
  → Deserialization
  → Feature Preprocessing
  → Model Prediction
  → PredictionEvent Serialization
  → Kafka Publish
  → Metrics Update
```

## Scalability

### Horizontal Scaling
- **Inference API**: Stateless, scale with load balancer
- **Streaming Consumer**: Scale up to # of Kafka partitions
- **Drift Monitor**: Single instance (maintains state)

### Vertical Scaling
- **Model Loading**: Memory-intensive, scale RAM
- **Batch Processing**: CPU-intensive, scale cores
- **ANN Inference**: GPU-accelerated (optional)

## Deployment Patterns

### Development
- docker-compose for all services
- Local Kafka and monitoring
- Hot-reload for code changes

### Staging
- Kubernetes cluster
- Managed Kafka (MSK, Confluent Cloud)
- Managed Prometheus/Grafana

### Production
- Multi-region Kubernetes
- Auto-scaling (HPA)
- Blue-green deployment
- Canary releases
- Disaster recovery plan

## Security Considerations

1. **API Security**: Rate limiting, authentication, HTTPS
2. **Data Security**: Encryption at rest and in transit
3. **Model Security**: Version control, integrity checks
4. **Network Security**: VPC isolation, firewall rules
5. **Secrets Management**: Vault, AWS Secrets Manager
