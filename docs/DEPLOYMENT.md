# Deployment Guide

## Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- 8GB+ RAM

### Quick Start

1. **Clone repository**
```bash
git clone <repository-url>
cd ai-ctids
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start infrastructure**
```bash
docker-compose up -d zookeeper kafka prometheus grafana
```

4. **Train models (local)**
```bash
python -m venv venv
source venv/bin/activate
pip install -r batch-trainer/requirements.txt

cd batch-trainer
python train.py --data-path ../data/cicids2017.csv --output-dir ../models
```

5. **Start services**
```bash
docker-compose up inference-api streaming-consumer drift-monitor
```

6. **Access UIs**
- API: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Production Deployment

### Option 1: Kubernetes

1. **Build and push images**
```bash
# Build all images
docker-compose build

# Tag and push
docker tag ai-ctids-inference:latest <registry>/ai-ctids-inference:v1.0.0
docker push <registry>/ai-ctids-inference:v1.0.0
```

2. **Deploy to Kubernetes**
```bash
# Create namespace
kubectl create namespace ai-ctids

# Apply configurations
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n ai-ctids
```

3. **Setup autoscaling**
```bash
kubectl apply -f k8s/hpa.yaml
```

### Option 2: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml ai-ctids

# Check services
docker service ls
```

### Option 3: AWS ECS/Fargate

1. **Create ECR repositories**
```bash
aws ecr create-repository --repository-name ai-ctids-inference
aws ecr create-repository --repository-name ai-ctids-consumer
```

2. **Push images to ECR**
```bash
# Login
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

# Tag and push
docker tag ai-ctids-inference:latest <account>.dkr.ecr.<region>.amazonaws.com/ai-ctids-inference:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/ai-ctids-inference:latest
```

3. **Create ECS task definitions and services**
```bash
aws ecs create-cluster --cluster-name ai-ctids
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
aws ecs create-service --cluster ai-ctids --service-name inference-api --task-definition ai-ctids-inference
```

## Monitoring Setup

### Grafana Dashboards

1. **Import dashboard**
- Navigate to http://localhost:3000
- Dashboards > Import
- Upload `observability/grafana/dashboards/ai-ctids-overview.json`

2. **Configure data source**
- Add Prometheus data source: http://prometheus:9090

### Alerts

Configure Alertmanager in `observability/alertmanager.yml`:

```yaml
route:
  receiver: 'email'
  group_by: ['alertname']

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@example.com'
        from: 'ai-ctids@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

## Scaling Considerations

### Horizontal Scaling

**Inference API**:
```bash
docker-compose up --scale inference-api=3
```

**Streaming Consumer**:
- Scale based on Kafka partition count
- One consumer per partition for maximum parallelism
```bash
docker-compose up --scale streaming-consumer=3
```

### Vertical Scaling

Update resource limits in docker-compose.yml:
```yaml
services:
  inference-api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Rollback Procedure

### Docker Compose
```bash
# Rollback to previous version
docker-compose down
docker pull <registry>/ai-ctids-inference:v0.9.0
docker-compose up -d
```

### Kubernetes
```bash
# Rollback deployment
kubectl rollout undo deployment/inference-api -n ai-ctids

# Rollback to specific revision
kubectl rollout undo deployment/inference-api --to-revision=2 -n ai-ctids
```

## Troubleshooting

### Model not loading
```bash
# Check model files exist
ls -lh models/

# Check logs
docker-compose logs inference-api
```

### Kafka connection issues
```bash
# Check Kafka is running
docker-compose ps kafka

# Test connectivity
docker exec -it ai-ctids_kafka_1 kafka-topics --list --bootstrap-server localhost:9092
```

### High latency
- Check Grafana dashboard for bottlenecks
- Increase worker count
- Enable GPU support (for ANN model)
