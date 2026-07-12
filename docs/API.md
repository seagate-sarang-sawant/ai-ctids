# AI-CTIDS API Documentation

## Inference API

Base URL: `http://localhost:8000`

### Endpoints

#### GET /
**Description**: Root endpoint with API information

**Response**:
```json
{
  "name": "AI-CTIDS Inference API",
  "version": "1.0.0",
  "model": "xgboost",
  "model_version": "latest",
  "status": "running"
}
```

#### GET /healthz
**Description**: Health check endpoint

**Response**: `200 OK`
```json
{
  "status": "healthy"
}
```

#### GET /readyz
**Description**: Readiness check - confirms model is loaded

**Response**: `200 OK` if ready, `503 Service Unavailable` if not
```json
{
  "status": "ready",
  "model": "xgboost",
  "model_version": "latest"
}
```

#### GET /metrics
**Description**: Prometheus metrics endpoint

**Response**: Plain text Prometheus format metrics

#### POST /predict
**Description**: Single network flow prediction

**Request Body**:
```json
{
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
  ...
}
```

**Response**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "predicted_label": "BENIGN",
  "predicted_label_encoded": 0,
  "confidence": 0.956,
  "probabilities": {
    "BENIGN": 0.956,
    "DoS Hulk": 0.023,
    "PortScan": 0.015,
    ...
  },
  "model_name": "xgboost",
  "model_version": "latest",
  "inference_time_ms": 12.3,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### POST /predict/batch
**Description**: Batch network flow predictions

**Request Body**:
```json
{
  "flows": [
    {
      "destination_port": 80,
      "flow_duration": 1234.5,
      ...
    },
    {
      "destination_port": 443,
      "flow_duration": 5678.9,
      ...
    }
  ]
}
```

**Response**:
```json
{
  "predictions": [
    {
      "request_id": "...",
      "predicted_label": "BENIGN",
      ...
    },
    {
      "request_id": "...",
      "predicted_label": "DoS Hulk",
      ...
    }
  ],
  "total_count": 2,
  "total_inference_time_ms": 25.6,
  "average_inference_time_ms": 12.8
}
```

## Example Usage

### Python
```python
import requests

# Single prediction
flow = {
    "destination_port": 80,
    "flow_duration": 1234.5,
    "total_fwd_packets": 10,
    ...
}

response = requests.post(
    "http://localhost:8000/predict",
    json=flow
)

prediction = response.json()
print(f"Threat: {prediction['predicted_label']}")
print(f"Confidence: {prediction['confidence']:.2%}")
```

### cURL
```bash
# Health check
curl http://localhost:8000/healthz

# Single prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "destination_port": 80,
    "flow_duration": 1234.5,
    ...
  }'

# Batch prediction
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "flows": [
      {...},
      {...}
    ]
  }'
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error: ..."
}
```

### 503 Service Unavailable
```json
{
  "detail": "Model not loaded - service not ready"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Prediction failed: ..."
}
```
