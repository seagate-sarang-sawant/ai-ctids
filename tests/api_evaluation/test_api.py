"""Test and evaluate the prediction API with real data.

This script:
1. Loads test datasets (validation, test, simulated)
2. Sends requests to the API (single and batch)
3. Computes evaluation metrics (accuracy, precision, recall, F1)
4. Generates evaluation reports
"""

import os
import sys
import argparse
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
import numpy as np
import requests
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config import settings, SELECTED_FEATURES, LABEL_MAPPING

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIEvaluator:
    """Evaluate the prediction API with test data."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.predictions = []
        self.ground_truth = []
        self.inference_times = []
    
    def check_api_health(self) -> bool:
        """Check if API is healthy and ready."""
        try:
            response = requests.get(f"{self.api_url}/healthz", timeout=5)
            if response.status_code != 200:
                logger.error(f"API health check failed: {response.status_code}")
                return False
            
            response = requests.get(f"{self.api_url}/readyz", timeout=5)
            if response.status_code != 200:
                logger.error(f"API readiness check failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
            
            logger.info("API is healthy and ready")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False
    
    def dataframe_row_to_api_format(self, row: pd.Series) -> Dict:
        """Convert DataFrame row to API request format.

        Converts CSV column names (Title_Case with special chars) to API format (snake_case).
        Also handles data quality issues like negative values for fields that require >= 0.

        Examples:
            Destination_Port -> destination_port
            Flow_Bytes/s -> flow_bytes_s
            Fwd_Packets/s -> fwd_packets_s
            Down/Up_Ratio -> down_up_ratio
        """
        feature_dict = {}
        for col in row.index:
            if col == 'Label':
                continue

            # Convert to snake_case and replace special characters
            # Replace / and spaces with underscores, then convert to lowercase
            api_key = col.replace('/', '_').replace(' ', '_').lower()

            try:
                value = float(row[col])

                # Handle invalid values based on field constraints
                # Most fields should be >= 0, but some like ratios can be negative
                # For fields that must be >= 0, clamp negative values to 0
                if value < 0 and api_key not in ['down_up_ratio']:
                    # Fields like init_win_bytes, packet lengths, counts should be >= 0
                    if any(keyword in api_key for keyword in [
                        'bytes', 'length', 'count', 'size', 'win', 'header',
                        'port', 'duration', 'packets', 'flags', 'variance',
                        'mean', 'std', 'max', 'min', 'total', 'avg', 'iat'
                    ]):
                        logger.warning(f"Clamping negative value to 0 for {col}: {value}")
                        value = 0.0

                feature_dict[api_key] = value
            except (ValueError, TypeError):
                # Skip non-numeric values
                logger.warning(f"Skipping non-numeric value for {col}: {row[col]}")
                continue

        return feature_dict
    
    def predict_single(self, flow_data: Dict, true_label: str = None) -> Dict:
        """Send single prediction request to API."""
        try:
            response = requests.post(
                f"{self.api_url}/predict",
                json=flow_data,
                timeout=30
            )
            response.raise_for_status()
            prediction = response.json()
            
            if true_label:
                self.ground_truth.append(true_label)
                self.predictions.append(prediction['predicted_label'])
                self.inference_times.append(prediction['inference_time_ms'])
            
            return prediction
        except Exception as e:
            logger.error(f"Single prediction failed: {e}")
            raise
    
    def predict_batch(self, flows: List[Dict], true_labels: List[str] = None) -> Dict:
        """Send batch prediction request to API."""
        try:
            request_data = {"flows": flows}
            response = requests.post(
                f"{self.api_url}/predict/batch",
                json=request_data,
                timeout=60
            )
            response.raise_for_status()
            batch_response = response.json()
            
            if true_labels:
                for pred, true_label in zip(batch_response['predictions'], true_labels):
                    self.ground_truth.append(true_label)
                    self.predictions.append(pred['predicted_label'])
                
                self.inference_times.append(batch_response['average_inference_time_ms'])
            
            return batch_response
        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            raise
    
    def evaluate_dataset(self, df: pd.DataFrame, batch_size: int = 32, use_batch_api: bool = True):
        """Evaluate API on a dataset.
        
        Args:
            df: DataFrame with network flow features and 'Label' column
            batch_size: Batch size for batch predictions
            use_batch_api: Use batch API if True, otherwise single predictions
        """
        logger.info(f"Evaluating on dataset with {len(df)} samples")
        logger.info(f"Using {'batch' if use_batch_api else 'single'} prediction API")
        
        start_time = time.time()
        
        if use_batch_api:
            # Batch prediction
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                flows = [self.dataframe_row_to_api_format(row) for _, row in batch_df.iterrows()]
                true_labels = batch_df['Label'].tolist()
                
                try:
                    self.predict_batch(flows, true_labels)
                    logger.info(f"Processed batch {i//batch_size + 1}/{(len(df)-1)//batch_size + 1}")
                except Exception as e:
                    logger.error(f"Failed to process batch {i//batch_size + 1}: {e}")
        else:
            # Single prediction
            for idx, (_, row) in enumerate(df.iterrows()):
                flow_data = self.dataframe_row_to_api_format(row)
                true_label = row['Label']
                
                try:
                    self.predict_single(flow_data, true_label)
                    if (idx + 1) % 100 == 0:
                        logger.info(f"Processed {idx + 1}/{len(df)} samples")
                except Exception as e:
                    logger.error(f"Failed to process sample {idx + 1}: {e}")
        
        total_time = time.time() - start_time
        logger.info(f"Completed evaluation in {total_time:.2f}s")
        logger.info(f"Average time per sample: {total_time/len(df)*1000:.2f}ms")

    def compute_metrics(self) -> Dict:
        """Compute evaluation metrics."""
        if not self.predictions or not self.ground_truth:
            logger.error("No predictions to evaluate")
            return {}

        logger.info(f"\n{'='*80}")
        logger.info("EVALUATION METRICS")
        logger.info(f"{'='*80}")

        metrics = {
            'accuracy': accuracy_score(self.ground_truth, self.predictions),
            'precision_macro': precision_score(self.ground_truth, self.predictions, average='macro', zero_division=0),
            'recall_macro': recall_score(self.ground_truth, self.predictions, average='macro', zero_division=0),
            'f1_macro': f1_score(self.ground_truth, self.predictions, average='macro', zero_division=0),
            'precision_weighted': precision_score(self.ground_truth, self.predictions, average='weighted', zero_division=0),
            'recall_weighted': recall_score(self.ground_truth, self.predictions, average='weighted', zero_division=0),
            'f1_weighted': f1_score(self.ground_truth, self.predictions, average='weighted', zero_division=0),
        }

        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.4f}")

        # Per-class metrics
        logger.info(f"\n{'='*80}")
        logger.info("CLASSIFICATION REPORT")
        logger.info(f"{'='*80}")
        report = classification_report(self.ground_truth, self.predictions)
        logger.info(f"\n{report}")

        # Confusion matrix
        logger.info(f"\n{'='*80}")
        logger.info("CONFUSION MATRIX")
        logger.info(f"{'='*80}")
        cm = confusion_matrix(self.ground_truth, self.predictions)
        logger.info(f"\n{cm}")

        # Inference time statistics
        if self.inference_times:
            logger.info(f"\n{'='*80}")
            logger.info("INFERENCE TIME STATISTICS")
            logger.info(f"{'='*80}")
            logger.info(f"Mean: {np.mean(self.inference_times):.2f}ms")
            logger.info(f"Median: {np.median(self.inference_times):.2f}ms")
            logger.info(f"Std: {np.std(self.inference_times):.2f}ms")
            logger.info(f"Min: {np.min(self.inference_times):.2f}ms")
            logger.info(f"Max: {np.max(self.inference_times):.2f}ms")
            logger.info(f"95th percentile: {np.percentile(self.inference_times, 95):.2f}ms")

        return metrics

    def save_results(self, output_path: str):
        """Save evaluation results to file."""
        results = {
            'metrics': self.compute_metrics(),
            'predictions': list(zip(self.ground_truth, self.predictions)),
            'inference_times_ms': self.inference_times
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved results to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Test and evaluate prediction API")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000",
                       help="API base URL")
    parser.add_argument("--data-path", type=str, required=True,
                       help="Path to test CSV file")
    parser.add_argument("--batch-size", type=int, default=32,
                       help="Batch size for batch predictions")
    parser.add_argument("--use-single-api", action="store_true",
                       help="Use single prediction API instead of batch")
    parser.add_argument("--output", type=str, default="./tests/api_evaluation/results.json",
                       help="Output path for results")

    args = parser.parse_args()

    # Create evaluator
    evaluator = APIEvaluator(api_url=args.api_url)

    # Check API health
    if not evaluator.check_api_health():
        logger.error("API is not ready. Please start the API and ensure models are loaded.")
        sys.exit(1)

    # Load test data
    logger.info(f"Loading test data from {args.data_path}")
    df = pd.read_csv(args.data_path)
    logger.info(f"Loaded {len(df)} samples")
    logger.info(f"Label distribution:\n{df['Label'].value_counts()}")

    # Evaluate
    evaluator.evaluate_dataset(
        df,
        batch_size=args.batch_size,
        use_batch_api=not args.use_single_api
    )

    # Compute and save metrics
    evaluator.compute_metrics()

    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    evaluator.save_results(args.output)

    logger.info("API evaluation complete!")


if __name__ == "__main__":
    main()

