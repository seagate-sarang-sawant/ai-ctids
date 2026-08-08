# API Evaluation Test Suite - Summary

## Overview

I've created a comprehensive API evaluation test suite for the AI-CTIDS prediction API. This suite allows you to test and evaluate your trained models using real validation data, test data, and simulated network flows.

## What Was Created

### 1. Test Data Preparation (`tests/api_evaluation/prepare_test_data.py`)
- Extracts validation and test sets from the CICIDS2017 dataset
- Applies the same preprocessing as the training pipeline
- Creates stratified samples to maintain label distribution
- Generates both full datasets (1000 samples) and small datasets (100 samples) for quick testing

### 2. Simulated Data Generator (`tests/api_evaluation/generate_simulated_data.py`)
- Generates synthetic network flows for different attack types
- Creates realistic BENIGN, DoS, DDoS, and PortScan flows
- Useful for testing model behavior on controlled data

### 3. API Test and Evaluation Script (`tests/api_evaluation/test_api.py`)
- Tests both single (`/predict`) and batch (`/predict/batch`) endpoints
- Computes comprehensive metrics:
  - Accuracy, Precision, Recall, F1 (macro and weighted)
  - Classification report per threat type
  - Confusion matrix
  - Inference time statistics (mean, median, std, percentiles)
- Saves results to JSON for further analysis

### 4. Quick Test Script (`tests/api_evaluation/quick_test.py`)
- Fast health check for the API
- Tests with a few sample predictions
- Validates both single and batch endpoints
- Perfect for quick validation after starting the API

### 5. Complete Test Suite Runner (`tests/api_evaluation/run_all_tests.py`)
- Orchestrates the entire evaluation workflow
- Prepares all test datasets
- Runs tests on validation, test, and simulated data
- Tests both batch and single API modes
- Generates comprehensive evaluation reports

### 6. Documentation
- **README.md** - Complete documentation of the test suite
- **USAGE_GUIDE.md** - Step-by-step usage instructions
- **API_EVALUATION_SUMMARY.md** - This summary document

### 7. Makefile Targets
Added convenient make targets:
- `make test-api-quick` - Quick API health and sample test
- `make test-api-prepare` - Prepare all test datasets
- `make test-api` - Run evaluation with validation set
- `make test-api-full` - Run complete evaluation suite

### 8. Updated Schema (`shared/schemas.py`)
- Enhanced `NetworkFlowEvent` to include all 63 features from CICIDS2017
- Added proper field aliases for special characters (/, etc.)
- Ensures API can accept all required features

## Quick Start Guide

### Step 1: Train Models (if not done)
```bash
make train
```

### Step 2: Start the API
```bash
# In a separate terminal
make api-dev
```

### Step 3: Run Quick Test
```bash
make test-api-quick
```

Expected output:
```
✓ Health check passed
✓ Readiness check passed
✓ Single prediction successful
  Predicted label: BENIGN
  Confidence: 0.9823
  Inference time: 12.45ms
✓ Batch prediction successful
  Total predictions: 5
  Average time per sample: 9.05ms
ALL TESTS PASSED! ✓
```

### Step 4: Prepare Test Data
```bash
make test-api-prepare
```

This creates test datasets in `tests/api_evaluation/data/`:
- `validation_set.csv` (1000 samples)
- `validation_small.csv` (100 samples)
- `test_set.csv` (1000 samples)
- `test_small.csv` (100 samples)
- `simulated_flows.csv` (500 samples)

### Step 5: Run Evaluation
```bash
# Quick evaluation with small dataset
make test-api

# Or complete evaluation suite
make test-api-full
```

### Step 6: Review Results
Check the results in `tests/api_evaluation/results_*.json`:
- `results_validation_batch.json` - Validation set with batch API
- `results_validation_single.json` - Validation set with single API
- `results_test_batch.json` - Test set results
- `results_simulated.json` - Simulated data results

## Evaluation Metrics

The test suite computes:

### Classification Metrics
- ✅ **Accuracy** - Overall prediction correctness
- ✅ **Precision** (macro & weighted) - Positive predictive value
- ✅ **Recall** (macro & weighted) - True positive rate
- ✅ **F1 Score** (macro & weighted) - Harmonic mean of precision/recall
- ✅ **Per-class Report** - Detailed metrics for each threat type
- ✅ **Confusion Matrix** - Prediction vs ground truth

### Performance Metrics
- ✅ **Mean Inference Time** - Average prediction time
- ✅ **Median Inference Time** - Median prediction time
- ✅ **95th Percentile** - 95% of predictions complete within this time
- ✅ **Min/Max** - Fastest and slowest predictions
- ✅ **Throughput** - Total samples processed per second

## Example Results

```
================================================================================
EVALUATION METRICS
================================================================================
accuracy: 0.9542
precision_macro: 0.8765
recall_macro: 0.8432
f1_macro: 0.8596

================================================================================
INFERENCE TIME STATISTICS
================================================================================
Mean: 12.34ms
Median: 11.23ms
95th percentile: 18.92ms
```

## Performance Targets

✅ **Good Performance**:
- Accuracy > 95%
- F1 macro > 85%
- Mean inference time < 20ms
- 95th percentile < 50ms

## Testing Different Scenarios

### 1. Test Different Models
```bash
# Update .env
MODEL_NAME=xgboost  # or logistic_regression, ann_model

# Restart API and test
make api-dev
make test-api
```

### 2. Test with Full Datasets
```bash
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/validation_set.csv \
    --batch-size 100 \
    --output ./results_full.json
```

### 3. Compare Batch vs Single API
The suite tests both automatically with `make test-api-full`, or manually:

```bash
# Batch API (faster)
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/test_small.csv \
    --batch-size 32

# Single API (baseline)
python3 tests/api_evaluation/test_api.py \
    --data-path ./tests/api_evaluation/data/test_small.csv \
    --use-single-api
```

## Files Created

```
tests/api_evaluation/
├── __init__.py
├── README.md                      # Complete documentation
├── USAGE_GUIDE.md                # Step-by-step usage guide
├── prepare_test_data.py          # Extract validation/test sets
├── generate_simulated_data.py    # Generate synthetic data
├── test_api.py                   # Main evaluation script
├── quick_test.py                 # Quick health check
├── run_all_tests.py              # Complete test suite runner
├── data/                         # Test datasets (generated)
└── results_*.json                # Evaluation results (generated)
```

## Next Steps

1. ✅ **Run Quick Test** - Verify API is working
2. ✅ **Prepare Data** - Create test datasets
3. ✅ **Run Evaluation** - Test with validation/test sets
4. ✅ **Analyze Results** - Review metrics and identify improvements
5. 🔄 **Iterate** - Retrain models based on findings
6. 📊 **Monitor** - Use for continuous evaluation in CI/CD

## Benefits

- ✅ **Comprehensive Testing** - Tests API with real, simulated, and edge-case data
- ✅ **Performance Metrics** - Measures both accuracy and inference speed
- ✅ **Easy to Use** - Simple make commands for common tasks
- ✅ **Reproducible** - Consistent test data and evaluation methodology
- ✅ **CI/CD Ready** - Can be integrated into automated testing pipelines
