# Complete API Evaluation Workflow

This guide shows the complete end-to-end workflow for evaluating your trained models using the prediction API.

## Prerequisites

- ✅ Python 3.8+
- ✅ Virtual environment activated
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ CICIDS2017 dataset in `data/cicids2017.csv`

## Step-by-Step Workflow

### Step 1: Train the Models

If you haven't trained the models yet:

```bash
cd batch-trainer
python3 train.py \
    --data-path ../data/cicids2017.csv \
    --output-dir ../models \
    --models logistic_regression xgboost ann
```

Or use the Makefile:

```bash
make train
```

This creates:
- `models/logistic_regression.pkl`
- `models/xgboost_model.pkl`
- `models/ann_model.keras`
- `models/standard_scaler.pkl`
- `models/label_encoder.pkl`
- `models/selected_features.pkl`

### Step 2: Start the Inference API

In a **separate terminal**:

```bash
cd inference-api
python3 main.py
```

Or use the Makefile:

```bash
make api-dev
```

The API will start at `http://localhost:8000`

You can check it's running by visiting:
- http://localhost:8000 - API info
- http://localhost:8000/docs - Interactive API documentation

### Step 3: Quick Health Check

In your **main terminal**, verify the API is working:

```bash
cd tests/api_evaluation
python3 quick_test.py
```

You should see:

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

================================================================================
ALL TESTS PASSED! ✓
================================================================================
```

### Step 4: Prepare Test Datasets

Extract validation and test sets from the real data:

```bash
python3 prepare_test_data.py \
    --data-path ../../data/cicids2017.csv \
    --output-dir ./data \
    --n-validation 1000 \
    --n-test 1000
```

Generate simulated data:

```bash
python3 generate_simulated_data.py \
    --n-samples 500 \
    --output ./data/simulated_flows.csv
```

Or use the Makefile:

```bash
make test-api-prepare
```

This creates:
- `data/validation_set.csv` (1000 samples)
- `data/validation_small.csv` (100 samples for quick tests)
- `data/test_set.csv` (1000 samples)
- `data/test_small.csv` (100 samples)
- `data/simulated_flows.csv` (500 synthetic samples)

### Step 5: Run API Evaluation

Test with the validation set:

```bash
python3 test_api.py \
    --data-path ./data/validation_small.csv \
    --batch-size 32 \
    --output ./results_validation.json
```

You'll see output like:

```
Loading test data from ./data/validation_small.csv
Loaded 100 samples
Label distribution:
BENIGN          50
DoS Hulk        20
PortScan        15
DDoS            10
DoS GoldenEye    5

Evaluating on dataset with 100 samples
Using batch prediction API
Processed batch 1/4
Processed batch 2/4
Processed batch 3/4
Processed batch 4/4
Completed evaluation in 1.23s

================================================================================
EVALUATION METRICS
================================================================================
accuracy: 0.9600
precision_macro: 0.8932
recall_macro: 0.8675
f1_macro: 0.8801
precision_weighted: 0.9584
recall_weighted: 0.9600
f1_weighted: 0.9591

================================================================================
CLASSIFICATION REPORT
================================================================================
                          precision    recall  f1-score   support

                 BENIGN       0.98      0.98      0.98        50
               DoS Hulk       0.95      0.90      0.92        20
               PortScan       0.87      0.87      0.87        15
                   DDoS       0.90      0.90      0.90        10
         DoS GoldenEye       0.83      0.83      0.83         5

                accuracy                           0.96       100
               macro avg       0.91      0.90      0.90       100
            weighted avg       0.96      0.96      0.96       100

================================================================================
INFERENCE TIME STATISTICS
================================================================================
Mean: 11.25ms
Median: 10.82ms
Std: 2.34ms
Min: 8.45ms
Max: 18.92ms
95th percentile: 15.67ms

Saved results to ./results_validation.json
```

### Step 6: Run Complete Evaluation Suite

For a comprehensive evaluation across all test datasets:

```bash
python3 run_all_tests.py
```

Or use the Makefile:

```bash
make test-api-full
```

This will:
1. ✅ Prepare all test datasets
2. ✅ Test with validation set (batch mode)
3. ✅ Test with validation set (single mode)
4. ✅ Test with test set
5. ✅ Test with simulated data
6. ✅ Generate comprehensive reports

Results will be saved to:
- `results_validation_batch.json`
- `results_validation_single.json`
- `results_test_batch.json`
- `results_simulated.json`

### Step 7: Visualize Results (Optional)

Create comparison plots:

```bash
python3 visualize_results.py \
    --results results_*.json \
    --output-dir ./
```

This generates:
- `metrics_comparison.png` - Side-by-side metric comparison
- `inference_times.png` - Inference time analysis

### Step 8: Analyze and Iterate

Review the results:

1. **Check Accuracy**: Should be >95% for good performance
2. **Check F1 Scores**: Macro F1 should be >85%
3. **Check Inference Times**: Mean should be <20ms for production readiness
4. **Review Confusion Matrix**: Identify misclassification patterns
5. **Per-Class Performance**: Check if any attack types are under-detected

If performance is not satisfactory:
- Retrain with different hyperparameters
- Try a different model (logistic_regression, xgboost, ann)
- Collect more training data
- Engineer new features

## Testing Different Models

### Test XGBoost
```bash
# Update .env
echo "MODEL_NAME=xgboost" > .env

# Restart API
make api-dev

# Run tests
make test-api
```

### Test Logistic Regression
```bash
echo "MODEL_NAME=logistic_regression" > .env
make api-dev
make test-api
```

### Test ANN
```bash
echo "MODEL_NAME=ann_model" > .env
make api-dev
make test-api
```

## Batch vs Single API Performance

Compare performance of batch vs single prediction:

```bash
# Batch API
python3 test_api.py \
    --data-path ./data/test_small.csv \
    --batch-size 32 \
    --output ./results_batch.json

# Single API
python3 test_api.py \
    --data-path ./data/test_small.csv \
    --use-single-api \
    --output ./results_single.json
```

Compare the `average_inference_time_ms` in both results to see the speedup from batching.

## Summary

After completing this workflow, you will have:

✅ Trained models evaluated on real validation data
✅ Performance metrics (accuracy, precision, recall, F1)
✅ Inference time statistics
✅ Comparison across different test datasets
✅ Identification of model strengths and weaknesses
✅ Data to support model selection and deployment decisions
