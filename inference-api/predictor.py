"""Model loading and prediction logic."""

import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import joblib
from prometheus_client import Counter, Histogram, Gauge

import sys
sys.path.append(str(Path(__file__).parent.parent))
from shared.schemas import NetworkFlowEvent, PredictionEvent, ThreatLabel
from shared.config import settings
from shared.feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)

# Prometheus metrics
PREDICTIONS_COUNTER = Counter('predictions_total', 'Total predictions made', ['model', 'label'])
PREDICTION_LATENCY = Histogram('prediction_latency_seconds', 'Prediction latency')
MODEL_LOAD_TIME = Gauge('model_load_time_seconds', 'Time taken to load model')


class ThreatPredictor:
    """Handle model loading and predictions."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_engineer = None
        self.label_encoder = None
        self.model_name = settings.MODEL_NAME
        self.model_version = settings.MODEL_VERSION
        self.is_ready = False
        
        if model_path is None:
            model_path = str(settings.MODEL_PATH)
        
        self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load trained model and preprocessing artifacts."""
        start_time = time.time()
        logger.info(f"Loading model from {model_path}")

        # Check if model file exists
        from pathlib import Path
        if not Path(model_path).exists():
            logger.warning(f"Model file not found at {model_path}. Service will start without a model.")
            logger.warning("Please train models using 'make train' and restart the service.")
            self.is_ready = False
            return

        try:
            # Load model
            if model_path.endswith('.keras'):
                import tensorflow as tf
                self.model = tf.keras.models.load_model(model_path)
            else:
                self.model = joblib.load(model_path)

            # Load preprocessing artifacts
            self.feature_engineer = FeatureEngineer()
            self.feature_engineer.load_artifacts(str(settings.MODELS_DIR))

            load_time = time.time() - start_time
            MODEL_LOAD_TIME.set(load_time)
            
            self.is_ready = True
            logger.info(f"Model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def preprocess_features(self, flow: NetworkFlowEvent) -> np.ndarray:
        """Preprocess single network flow for prediction."""
        # Convert to feature dictionary
        features_dict = flow.to_feature_dict()
        
        # Ensure all required features are present
        if self.feature_engineer.selected_features:
            features = [features_dict.get(f, 0.0) for f in self.feature_engineer.selected_features]
        else:
            features = list(features_dict.values())
        
        # Convert to array and scale
        X = np.array(features).reshape(1, -1)
        X_scaled = self.feature_engineer.scale_features(X, fit=False)
        
        return X_scaled
    
    def predict_single(self, flow: NetworkFlowEvent) -> PredictionEvent:
        """Make prediction for single network flow."""
        with PREDICTION_LATENCY.time():
            start_time = time.time()
            
            # Preprocess
            X = self.preprocess_features(flow)
            
            # Predict
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                pred_idx = np.argmax(proba)
            else:  # Keras model
                proba = self.model.predict(X, verbose=0)[0]
                pred_idx = np.argmax(proba)
            
            # Decode prediction
            pred_label = self.feature_engineer.label_encoder.inverse_transform([pred_idx])[0]
            
            # Build probability dict
            prob_dict = {
                self.feature_engineer.label_encoder.inverse_transform([i])[0]: float(p)
                for i, p in enumerate(proba)
            }
            
            inference_time_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            PREDICTIONS_COUNTER.labels(model=self.model_name, label=pred_label).inc()
            
            # Create prediction event
            prediction = PredictionEvent(
                request_id=flow.correlation_id or "unknown",
                predicted_label=ThreatLabel(pred_label),
                predicted_label_encoded=int(pred_idx),
                confidence=float(proba[pred_idx]),
                probabilities=prob_dict,
                model_name=self.model_name,
                model_version=self.model_version,
                inference_time_ms=inference_time_ms
            )
            
            return prediction
    
    def predict_batch(self, flows: List[NetworkFlowEvent]) -> List[PredictionEvent]:
        """Make predictions for batch of network flows."""
        predictions = []
        total_start = time.time()
        
        # Preprocess all flows
        X_batch = np.vstack([self.preprocess_features(flow) for flow in flows])
        
        # Batch prediction
        if hasattr(self.model, 'predict_proba'):
            proba_batch = self.model.predict_proba(X_batch)
        else:  # Keras model
            proba_batch = self.model.predict(X_batch, verbose=0)
        
        # Create prediction events
        for flow, proba in zip(flows, proba_batch):
            pred_idx = np.argmax(proba)
            pred_label = self.feature_engineer.label_encoder.inverse_transform([pred_idx])[0]
            
            prob_dict = {
                self.feature_engineer.label_encoder.inverse_transform([i])[0]: float(p)
                for i, p in enumerate(proba)
            }
            
            prediction = PredictionEvent(
                request_id=flow.correlation_id or "unknown",
                predicted_label=ThreatLabel(pred_label),
                predicted_label_encoded=int(pred_idx),
                confidence=float(proba[pred_idx]),
                probabilities=prob_dict,
                model_name=self.model_name,
                model_version=self.model_version,
                inference_time_ms=0  # Will be set below
            )
            
            predictions.append(prediction)
            PREDICTIONS_COUNTER.labels(model=self.model_name, label=pred_label).inc()
        
        # Calculate average inference time
        total_time_ms = (time.time() - total_start) * 1000
        avg_time_ms = total_time_ms / len(flows)
        
        for pred in predictions:
            pred.inference_time_ms = avg_time_ms
        
        return predictions
