"""Model evaluation and metadata generation.

Computes comprehensive metrics, calibration, and generates deployment metadata.
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, log_loss, confusion_matrix,
    calibration_curve, classification_report
)
from sklearn.calibration import CalibrationDisplay

import sys
sys.path.append(str(Path(__file__).parent.parent))
from shared.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Comprehensive model evaluation with calibration and metadata generation."""
    
    def __init__(self, model_path: str, model_type: str = "xgboost"):
        self.model_path = Path(model_path)
        self.model_type = model_type
        self.model_dir = self.model_path.parent
        
        # Load model
        if model_type == "ann":
            import tensorflow as tf
            self.model = tf.keras.models.load_model(model_path)
        else:
            self.model = joblib.load(model_path)
        
        logger.info(f"Loaded {model_type} model from {model_path}")
    
    def evaluate(self, X_test, y_test) -> Dict[str, Any]:
        """Compute comprehensive evaluation metrics."""
        logger.info("Computing evaluation metrics...")
        
        # Predictions
        if self.model_type == "ann":
            y_proba = self.model.predict(X_test)
            y_pred = np.argmax(y_proba, axis=1)
        else:
            y_pred = self.model.predict(X_test)
            y_proba = self.model.predict_proba(X_test)
        
        # Classification metrics
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision_macro": float(precision_score(y_test, y_pred, average='macro', zero_division=0)),
            "precision_weighted": float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
            "recall_macro": float(recall_score(y_test, y_pred, average='macro', zero_division=0)),
            "recall_weighted": float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
            "f1_macro": float(f1_score(y_test, y_pred, average='macro', zero_division=0)),
            "f1_weighted": float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
        }
        
        # ROC AUC
        try:
            metrics["roc_auc_macro"] = float(roc_auc_score(y_test, y_proba, multi_class='ovr', average='macro'))
            metrics["roc_auc_weighted"] = float(roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted'))
        except Exception as e:
            logger.warning(f"Could not compute ROC AUC: {e}")
        
        # Log loss
        try:
            metrics["log_loss"] = float(log_loss(y_test, y_proba))
        except Exception as e:
            logger.warning(f"Could not compute log loss: {e}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics["confusion_matrix"] = cm.tolist()
        
        logger.info("Evaluation metrics computed successfully")
        for key, value in metrics.items():
            if key != "confusion_matrix":
                logger.info(f"  {key}: {value:.4f}")
        
        return metrics, y_pred, y_proba
    
    def compute_calibration(self, y_test, y_proba, n_bins: int = 10) -> Dict[str, Any]:
        """Compute calibration error for probabilistic predictions."""
        logger.info("Computing calibration metrics...")
        
        calibration_metrics = {}
        
        # For each class, compute calibration
        n_classes = y_proba.shape[1]
        ece_scores = []
        
        for class_idx in range(n_classes):
            # Binary calibration for this class
            y_binary = (y_test == class_idx).astype(int)
            prob_pos = y_proba[:, class_idx]
            
            try:
                fraction_of_positives, mean_predicted_value = calibration_curve(
                    y_binary, prob_pos, n_bins=n_bins, strategy='uniform'
                )
                
                # Expected Calibration Error (ECE)
                ece = np.abs(fraction_of_positives - mean_predicted_value).mean()
                ece_scores.append(ece)
            except Exception as e:
                logger.warning(f"Calibration failed for class {class_idx}: {e}")
        
        if ece_scores:
            calibration_metrics["expected_calibration_error"] = float(np.mean(ece_scores))
            calibration_metrics["max_calibration_error"] = float(np.max(ece_scores))
        
        logger.info(f"  ECE: {calibration_metrics.get('expected_calibration_error', 'N/A')}")
        
        return calibration_metrics
    
    def save_metadata(self, metrics: Dict[str, Any], calibration: Dict[str, Any]):
        """Save evaluation metadata as JSON."""
        metadata = {
            "model_type": self.model_type,
            "model_path": str(self.model_path.name),
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "calibration": calibration,
            "config": {
                "random_seed": settings.RANDOM_SEED,
                "model_version": settings.MODEL_VERSION,
            }
        }
        
        # Save metadata
        metadata_path = self.model_dir / f"{self.model_path.stem}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {metadata_path}")
        return metadata_path
    
    def run_evaluation(self, X_test, y_test):
        """Run complete evaluation pipeline."""
        # Evaluate
        metrics, y_pred, y_proba = self.evaluate(X_test, y_test)
        
        # Calibration
        calibration = self.compute_calibration(y_test, y_proba)
        
        # Save metadata
        metadata_path = self.save_metadata(metrics, calibration)
        
        logger.info("Evaluation completed successfully!")
        return metrics, calibration, metadata_path


def main():
    """Main evaluation entry point."""
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained model")
    parser.add_argument("--model-type", type=str, default="xgboost", 
                       choices=["logistic_regression", "xgboost", "ann"])
    parser.add_argument("--test-data", type=str, required=True, help="Path to test data")
    
    args = parser.parse_args()
    
    # Load test data (assuming preprocessed)
    logger.info(f"Loading test data from {args.test_data}")
    # Implementation depends on test data format
    
    evaluator = ModelEvaluator(args.model_path, args.model_type)
    # results = evaluator.run_evaluation(X_test, y_test)


if __name__ == "__main__":
    main()
