# API Evaluation Test Suite

This directory contains comprehensive tests for evaluating the AI-CTIDS prediction API with validation sets, test sets, and simulated data.

## Overview

The test suite includes:

1. **Test Data Preparation** - Extract validation and test sets from real CICIDS2017 data
2. **Simulated Data Generation** - Generate synthetic network flows for different attack types
3. **API Testing** - Test both single and batch prediction endpoints
4. **Metrics Computation** - Calculate accuracy, precision, recall, F1, and inference time statistics

## Files

```
api_evaluation/
├── README.md                      # This file
├── prepare_test_data.py          # Prepare validation/test sets from real data
├── generate_simulated_data.py    # Generate synthetic test data
├── test_api.py                   # Main API testing and evaluation script
├── run_all_tests.py              # Run complete test suite
├── data/                         # Test datasets (generated)
│   ├── validation_set.csv
│   ├── validation_small.csv
│   ├── test_set.csv
│   ├── test_small.csv
│   └── simulated_flows.csv
└── results_*.json                # Evaluation results (generated)
```

## Quick Start

### Prerequisites

1. **Train Models** (if not already done):
```bash
cd batch-trainer
python3 train.py --data-path ../data/cicids2017.csv --output-dir ../models
```

2. **Start the API**:
```bash
cd inference-api
python3 main.py
```

The API should be running at `http://localhost:8000`.

### Run All Tests

The easiest way to run the complete evaluation:

```bash
cd tests/api_evaluation
python3 run_all_tests.py
```

This will:
1. Prepare test datasets
2. Generate simulated data
3. Test API with validation set (batch and single modes)
4. Test API with test set
5. Test API with simulated data
6. Generate evaluation reports

### Run Individual Tests

#### 1. Prepare Test Data

Extract validation and test sets from the full dataset:

```bash
python3 prepare_test_data.py \
    --data-path ../../data/cicids2017.csv \
    --output-dir ./data \
    --n-validation 1000 \
    --n-test 1000
```

This creates:
- `validation_set.csv` - 1000 samples for validation
- `validation_small.csv` - 100 samples for quick testing
- `test_set.csv` - 1000 samples for testing
- `test_small.csv` - 100 samples for quick testing

#### 2. Generate Simulated Data

Create synthetic network flows:

```bash
python3 generate_simulated_data.py \
    --n-samples 500 \
    --output ./data/simulated_flows.csv
```

#### 3. Test API with Batch Predictions

```bash
python3 test_api.py \
    --data-path ./data/validation_small.csv \
    --batch-size 32 \
    --output ./results_validation.json
```

#### 4. Test API with Single Predictions

```bash
python3 test_api.py \
    --data-path ./data/validation_small.csv \
    --use-single-api \
    --output ./results_validation_single.json
```

## Evaluation Metrics

The test suite computes the following metrics:

### Classification Metrics
- **Accuracy** - Overall prediction accuracy
- **Precision** (macro & weighted) - Precision across all classes
- **Recall** (macro & weighted) - Recall across all classes
- **F1 Score** (macro & weighted) - Harmonic mean of precision and recall
- **Per-class metrics** - Detailed report for each threat type
- **Confusion Matrix** - Predicted vs actual labels

### Performance Metrics
- **Mean inference time** - Average time per prediction
- **Median inference time** - Median prediction time
- **95th percentile** - 95% of predictions complete within this time
- **Min/Max** - Fastest and slowest predictions

## Example Output

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

## Troubleshooting

### API Not Ready

If you get "API is not ready" errors:
1. Check if the API is running: `curl http://localhost:8000/healthz`
2. Check if models are loaded: `curl http://localhost:8000/readyz`
3. Verify model files exist in `models/` directory

### Schema Validation Errors

If you get Pydantic validation errors, ensure:
1. All 63 required features are present in the test data
2. Feature names match the expected format
3. Values are within valid ranges

### Connection Errors

If API connection fails:
1. Verify API is running on the correct port
2. Check firewall settings
3. Use `--api-url` flag to specify custom URL

## Advanced Usage

### Test Specific Models

Test different models by changing the `MODEL_NAME` in your `.env` file:

```bash
# .env
MODEL_NAME=xgboost  # or logistic_regression, ann_model
```

Restart the API for changes to take effect.

### Custom Batch Sizes

Test with different batch sizes to find optimal throughput:

```bash
for batch_size in 1 16 32 64 128; do
    python3 test_api.py \
        --data-path ./data/test_set.csv \
        --batch-size $batch_size \
        --output ./results_batch_${batch_size}.json
done
```

### Large-Scale Testing

For testing with the full validation/test sets:

```bash
python3 test_api.py \
    --data-path ./data/validation_set.csv \
    --batch-size 100 \
    --output ./results_validation_full.json
```

## Results Interpretation

### Good Model Performance
- Accuracy > 95%
- F1 macro > 85%
- Inference time < 20ms per sample

### API Performance Targets
- Single prediction: < 50ms
- Batch prediction (32 samples): < 500ms (< 16ms per sample)
- 95th percentile: < 100ms

## Next Steps

After running evaluations:
1. Review metrics to identify areas for improvement
2. Analyze confusion matrix for common misclassifications
3. Test with production-like load using load testing tools
4. Monitor API metrics in Grafana dashboard
