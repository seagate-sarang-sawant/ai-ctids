# AI-CTIDS Requirements Guide

This document explains the dependency management structure for the AI-CTIDS project.

## 📁 Requirements Files Overview

| File | Purpose | Use Case |
|------|---------|----------|
| `requirements.txt` | **Complete installation** | Full development + production environment |
| `requirements-dev.txt` | **Development tools** | Includes testing, linting, profiling, docs |
| `requirements-minimal.txt` | **Production-only** | Lightweight deployment (inference-api only) |
| `*/requirements.txt` | **Service-specific** | Individual microservice dependencies |

## 🎯 Which File Should I Use?

### For Local Development
```bash
# Full installation (recommended for contributors)
pip install -r requirements.txt

# Or with development tools
pip install -r requirements-dev.txt
```

### For Production Deployment
```bash
# Minimal installation (inference API only)
pip install -r requirements-minimal.txt

# Or full stack
pip install -r requirements.txt
```

### For Specific Services
```bash
# Training pipeline only
pip install -r batch-trainer/requirements.txt

# Inference API only
pip install -r inference-api/requirements.txt

# Streaming consumer only
pip install -r streaming-consumer/requirements.txt
```

### For Jupyter Notebooks
```bash
# Install complete requirements
pip install -r requirements.txt

# The notebook uses:
# - pandas, numpy (data manipulation)
# - scikit-learn (preprocessing, models)
# - xgboost (gradient boosting)
# - tensorflow (deep learning)
# - matplotlib, seaborn (visualization)
# - shap (model interpretation)
```

## 📦 Dependency Sources

### From Jupyter Notebook
The following dependencies are extracted from the research notebook:

```python
# Data manipulation
import pandas as pd
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# ML utilities
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Advanced ML
from xgboost import XGBClassifier

# Deep learning
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout

# Explainability
import shap

# Persistence
import joblib
```

### From Service Requirements
Each service has its own `requirements.txt`:

- **batch-trainer/** - Training pipeline + W&B tracking
- **inference-api/** - FastAPI + model serving
- **streaming-consumer/** - Kafka + real-time inference
- **data-ingestion/** - Kafka producer + data simulation
- **drift-monitor/** - PSI calculation + monitoring
- **preprocessing-service/** - Feature engineering service
- **shared/** - Common utilities

## 🔧 Installation Methods

### Method 1: Direct pip install
```bash
pip install -r requirements.txt
```

### Method 2: Using virtual environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Method 3: Using conda
```bash
# Create conda environment
conda create -n ai-ctids python=3.10

# Activate environment
conda activate ai-ctids

# Install dependencies
pip install -r requirements.txt
```

### Method 4: Using uv (fastest)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt
```

### Method 5: Using Docker
```bash
# Each service has its own Dockerfile
docker build -t ai-ctids-api -f inference-api/Dockerfile .

# Or use docker-compose for all services
docker-compose up --build
```

## 📊 Dependency Tree

```
requirements.txt (root)
├── Core ML Stack
│   ├── numpy>=1.24.0
│   ├── pandas>=2.0.0
│   ├── scikit-learn>=1.3.0
│   ├── xgboost>=2.0.0
│   └── tensorflow>=2.15.0
├── Visualization (Notebook)
│   ├── matplotlib>=3.7.0
│   └── seaborn>=0.12.0
├── API Framework
│   ├── fastapi>=0.109.0
│   └── uvicorn>=0.27.0
├── Streaming
│   └── confluent-kafka>=2.3.0
├── Monitoring
│   └── prometheus-client>=0.19.0
├── Experiment Tracking
│   └── wandb>=0.16.0
└── Utilities
    ├── pydantic>=2.0.0
    ├── joblib>=1.3.0
    ├── shap>=0.44.0
    └── python-dotenv>=1.0.0
```

## 🔒 Version Constraints

All dependencies use **compatible release** version constraints:

```
package>=X.Y.Z,<(X+1).0.0  # Allow minor updates, prevent major breaking changes
```

**Why?**
- ✅ Allows bug fixes and minor improvements
- ✅ Prevents breaking changes from major version updates
- ✅ Reproducible builds
- ❌ May miss performance improvements in new major versions

## 🐛 Troubleshooting

### Issue: TensorFlow installation fails

**macOS Apple Silicon (M1/M2):**
```bash
pip install tensorflow-macos tensorflow-metal
```

**Windows (no native GPU support):**
```bash
# Use WSL2 or Docker
docker run -it tensorflow/tensorflow:latest-gpu bash
```

**Linux with CUDA:**
```bash
# Ensure CUDA 11.8+ is installed
pip install tensorflow[and-cuda]
```

### Issue: Confluent-kafka fails to build

**macOS:**
```bash
brew install librdkafka
pip install confluent-kafka
```

**Ubuntu/Debian:**
```bash
sudo apt-get install librdkafka-dev
pip install confluent-kafka
```

### Issue: XGBoost GPU support

```bash
# Install GPU version
pip install xgboost[gpu]

# Or build from source
git clone --recursive https://github.com/dmlc/xgboost
cd xgboost && mkdir build && cd build
cmake .. -DUSE_CUDA=ON
make -j4
cd ../python-package
pip install -e .
```

### Issue: Version conflicts

```bash
# Create fresh environment
python3 -m venv fresh_env
source fresh_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 📝 Updating Dependencies

### Check for outdated packages
```bash
pip list --outdated
```

### Update specific package
```bash
pip install --upgrade package-name
```

### Generate locked requirements
```bash
pip freeze > requirements-lock.txt
```

### Security audit
```bash
pip install safety
safety check -r requirements.txt
```

## 🚀 Production Best Practices

### 1. Use requirements-lock.txt in production
```bash
# Development: generate lock file
pip freeze > requirements-lock.txt

# Production: install exact versions
pip install -r requirements-lock.txt
```

### 2. Layer Docker images efficiently
```dockerfile
# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code later (changes frequently)
COPY . .
```

### 3. Use multi-stage builds
```dockerfile
# Build stage
FROM python:3.10-slim as builder
RUN pip wheel -r requirements.txt

# Runtime stage
FROM python:3.10-slim
COPY --from=builder /wheels /wheels
RUN pip install /wheels/*
```

## 📚 Related Documentation

- [Architecture](ARCHITECTURE.md) - System design overview
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Development Guide](../CONTRIBUTING.md) - Contributing guidelines
- [API Documentation](API.md) - REST API reference

## 🔗 External Resources

- [pip documentation](https://pip.pypa.io/)
- [virtualenv guide](https://virtualenv.pypa.io/)
- [conda documentation](https://docs.conda.io/)
- [Docker best practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python packaging guide](https://packaging.python.org/)
