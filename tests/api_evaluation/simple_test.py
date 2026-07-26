"""Simple test to verify API is working with a few samples."""

import sys
import pandas as pd
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

# Load test data
df = pd.read_csv('tests/api_evaluation/data/validation_small.csv')
print(f"Loaded {len(df)} samples from validation set")
print(f"\nLabel distribution:\n{df['Label'].value_counts()}")

# Take first 5 samples
test_samples = df.head(5)

print("\n" + "="*80)
print("Testing API with 5 samples")
print("="*80)

# Convert first sample to API format
def convert_to_api_format(row):
    """Convert DataFrame row to API format."""
    feature_dict = {}
    for col in row.index:
        if col == 'Label':
            continue
        api_key = col.replace('/', '_').replace(' ', '_').lower()
        value = float(row[col])

        # Clamp negative values to 0 for fields that require >= 0
        if value < 0 and api_key not in ['down_up_ratio']:
            if any(keyword in api_key for keyword in [
                'bytes', 'length', 'count', 'size', 'win', 'header',
                'port', 'duration', 'packets', 'flags', 'variance',
                'mean', 'std', 'max', 'min', 'total', 'avg', 'iat'
            ]):
                value = 0.0

        feature_dict[api_key] = value
    return feature_dict

# Test each sample
for idx, (_, row) in enumerate(test_samples.iterrows(), 1):
    flow_data = convert_to_api_format(row)
    true_label = row['Label']
    
    print(f"\nSample {idx}:")
    print(f"  True label: {true_label}")
    
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json=flow_data,
            timeout=10
        )
        
        if response.status_code == 200:
            prediction = response.json()
            predicted_label = prediction['predicted_label']
            confidence = prediction['confidence']
            inference_time = prediction['inference_time_ms']
            
            match = "✓" if predicted_label == true_label else "✗"
            print(f"  Predicted: {predicted_label} (confidence: {confidence:.4f}) {match}")
            print(f"  Inference time: {inference_time:.2f}ms")
        else:
            print(f"  Error: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Failed: {e}")

print("\n" + "="*80)
print("Test complete!")
print("="*80)
