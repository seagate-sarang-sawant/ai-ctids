# API Evaluation Usage Guide

## Quick Start

### 1. Start the API

First, ensure your models are trained and the API is running:

```bash
# If models aren't trained yet
make train

# Start the API (in a separate terminal)
make api-dev
```

### 2. Run Quick Test

Verify the API is working with a quick health check and sample predictions:

```bash
make test-api-quick
```

Or directly:

```bash
python3 tests/api_evaluation/quick_test.py
```

Expected output:
```
================================================================================
AI-CTIDS API QUICK TEST
================================================================================
Testing health endpoints...
✓ Health check passed
✓ Readiness check passed
  Model info: {'status': 'ready', 'model': 'xgboost', 'model_version': 'latest'}

Testing single prediction endpoint...
✓ Single prediction successful
  Predicted label: BENIGN
  Confidence: 0.9823
  Inference time: 12.45ms

Testing batch prediction endpoint...
✓ Batch prediction successful
  Total predictions: 5
  Total time: 45.23ms
  Average time per sample: 9.05ms
  First prediction: BENIGN (confidence: 0.9823)

================================================================================
ALL TESTS PASSED! ✓
================================================================================
```

### 3. Prepare Test Data

Prepare validation and test datasets from the real CICIDS2017 data:

```bash
make test-api-prepare
```

This creates:
- `tests/api_evaluation/data/validation_set.csv` (1000 samples)
- `tests/api_evaluation/data/validation_small.csv` (100 samples)
- `tests/api_evaluation/data/test_set.csv` (1000 samples)
- `tests/api_evaluation/data/test_small.csv` (100 samples)
- `tests/api_evaluation/data/simulated_flows.csv` (500 samples)

### 4. Run API Evaluation

Test the API with real validation data:

```bash
make test-api
```

Or directly:

```bash
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/validation_small.csv \
    --batch-size 32 \
    --output ./tests/api_evaluation/results_validation.json
```

### 5. Run Complete Evaluation Suite

Run all tests (validation, test, simulated data, batch & single API):

```bash
make test-api-full
```

Or directly:

```bash
python3 tests/api_evaluation/run_all_tests.py
```

## Understanding the Results

After running evaluations, you'll see output like:

```
================================================================================
EVALUATION METRICS
================================================================================
accuracy: 0.9542
precision_macro: 0.8765
recall_macro: 0.8432
f1_macro: 0.8596
precision_weighted: 0.9523
recall_weighted: 0.9542
f1_weighted: 0.9531

================================================================================
CLASSIFICATION REPORT
================================================================================
                          precision    recall  f1-score   support

                 BENIGN       0.98      0.99      0.99       450
               DoS Hulk       0.95      0.93      0.94       120
               PortScan       0.87      0.85      0.86       100
                   DDoS       0.92      0.90      0.91        80
         DoS GoldenEye       0.89      0.87      0.88        50

                accuracy                           0.95      1000
               macro avg       0.92      0.91      0.92      1000
            weighted avg       0.95      0.95      0.95      1000

================================================================================
INFERENCE TIME STATISTICS
================================================================================
Mean: 12.34ms
Median: 11.23ms
Std: 3.45ms
Min: 8.12ms
Max: 25.67ms
95th percentile: 18.92ms
```

### Key Metrics Explained

- **Accuracy**: Overall correctness (target: >95%)
- **Precision**: Of predicted attacks, how many were actual attacks
- **Recall**: Of actual attacks, how many were detected
- **F1 Score**: Harmonic mean of precision and recall
- **Inference Time**: How fast predictions are made

### Performance Targets

✅ **Good Performance**:
- Accuracy > 95%
- F1 macro > 85%
- Mean inference time < 20ms
- 95th percentile < 50ms

⚠️ **Needs Improvement**:
- Accuracy < 90%
- F1 macro < 75%
- Mean inference time > 50ms

## Advanced Usage

### Test Different Models

Change the model in `.env`:

```bash
# .env
MODEL_NAME=xgboost  # or logistic_regression, ann_model
```

Restart the API and re-run tests.

### Test with Full Datasets

```bash
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/validation_set.csv \
    --batch-size 100 \
    --output ./tests/api_evaluation/results_validation_full.json
```

### Compare Batch vs Single API Performance

```bash
# Batch API
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/test_small.csv \
    --batch-size 32 \
    --output ./results_batch.json

# Single API
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/test_small.csv \
    --use-single-api \
    --output ./results_single.json
```

Compare the inference times to see the benefit of batching.

## Troubleshooting

### "API is not ready"

1. Check if API is running: `curl http://localhost:8000/healthz`
2. Check if models exist: `ls models/`
3. Train models if missing: `make train`

### "Connection refused"

- Ensure API is running: `make api-dev`
- Check the port (default: 8000)

### "Validation error" or "Schema mismatch"

- Ensure test data has all 63 required features
- Check feature names match expected format
- Re-run `make test-api-prepare` to regenerate clean data

## Files Generated

After running tests, you'll find:

```
tests/api_evaluation/
├── data/
│   ├── validation_set.csv
│   ├── validation_small.csv
│   ├── test_set.csv
│   ├── test_small.csv
│   └── simulated_flows.csv
└── results_*.json
    ├── results_validation_batch.json
    ├── results_validation_single.json
    ├── results_test_batch.json
    └── results_simulated.json
```
