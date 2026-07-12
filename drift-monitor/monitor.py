"""Drift monitoring service with Population Stability Index (PSI) calculation.

Monitors feature distributions and alerts when drift exceeds threshold.
"""

import argparse
import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Deque

import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaError
from prometheus_client import Gauge, Counter, start_http_server

import sys
sys.path.append(str(Path(__file__).parent.parent))
from shared.schemas import PredictionEvent, NetworkFlowEvent
from shared.config import settings, SELECTED_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
PSI_GAUGE = Gauge('drift_psi_score', 'Population Stability Index', ['feature'])
DRIFT_ALERTS = Counter('drift_alerts_total', 'Total drift alerts', ['feature'])
SAMPLES_PROCESSED = Counter('drift_monitor_samples_processed', 'Samples processed')


class PopulationStabilityIndex:
    """Calculate Population Stability Index for drift detection."""
    
    @staticmethod
    def calculate_psi(
        reference_dist: np.ndarray,
        current_dist: np.ndarray,
        epsilon: float = 1e-10
    ) -> float:
        """Calculate PSI between two distributions.
        
        PSI = Σ (current% - reference%) * ln(current% / reference%)
        
        Args:
            reference_dist: Reference distribution (training)
            current_dist: Current distribution (production)
            epsilon: Small value to avoid division by zero
        
        Returns:
            PSI score (0 = no drift, >0.2 = significant drift)
        """
        # Ensure distributions sum to 1
        reference_dist = reference_dist / (reference_dist.sum() + epsilon)
        current_dist = current_dist / (current_dist.sum() + epsilon)
        
        # Add epsilon to avoid log(0)
        reference_dist = reference_dist + epsilon
        current_dist = current_dist + epsilon
        
        # Calculate PSI
        psi = np.sum(
            (current_dist - reference_dist) * np.log(current_dist / reference_dist)
        )
        
        return float(psi)
    
    @staticmethod
    def bin_data(data: np.ndarray, n_bins: int = 10) -> np.ndarray:
        """Bin continuous data into discrete buckets.
        
        Args:
            data: Input data
            n_bins: Number of bins
        
        Returns:
            Histogram counts
        """
        if len(data) == 0:
            return np.zeros(n_bins)
        
        # Use percentile-based binning for robustness
        bins = np.percentile(data, np.linspace(0, 100, n_bins + 1))
        bins = np.unique(bins)  # Remove duplicates
        
        if len(bins) <= 1:
            # All values are the same
            counts = np.zeros(n_bins)
            counts[0] = len(data)
            return counts
        
        hist, _ = np.histogram(data, bins=bins)
        
        # Pad to n_bins if needed
        if len(hist) < n_bins:
            hist = np.pad(hist, (0, n_bins - len(hist)))
        
        return hist[:n_bins]


class DriftMonitor:
    """Monitor feature drift using rolling windows and PSI."""
    
    def __init__(
        self,
        reference_data_path: str,
        window_size: int = 10000,
        psi_threshold: float = 0.2,
        check_interval: int = 300
    ):
        self.window_size = window_size
        self.psi_threshold = psi_threshold
        self.check_interval = check_interval
        
        # Rolling windows for each feature
        self.feature_windows: Dict[str, Deque[float]] = {
            feature: deque(maxlen=window_size)
            for feature in SELECTED_FEATURES
        }
        
        # Load reference distributions
        logger.info(f"Loading reference data from {reference_data_path}")
        self.reference_distributions = self._load_reference_data(reference_data_path)
        logger.info(f"Loaded reference distributions for {len(self.reference_distributions)} features")
        
        self.last_check_time = time.time()
    
    def _load_reference_data(self, data_path: str) -> Dict[str, np.ndarray]:
        """Load and compute reference distributions from training data."""
        df = pd.read_csv(data_path)
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.replace(" ", "_", regex=False)
        
        distributions = {}
        for feature in SELECTED_FEATURES:
            if feature in df.columns:
                data = df[feature].dropna().values
                # Bin data for PSI calculation
                hist = PopulationStabilityIndex.bin_data(data, n_bins=10)
                distributions[feature] = hist
            else:
                logger.warning(f"Feature {feature} not found in reference data")
        
        return distributions
    
    def add_sample(self, sample: Dict[str, float]):
        """Add new sample to rolling windows."""
        for feature, value in sample.items():
            if feature in self.feature_windows:
                self.feature_windows[feature].append(value)
        
        SAMPLES_PROCESSED.inc()
    
    def check_drift(self) -> Dict[str, float]:
        """Check for drift in all features.
        
        Returns:
            Dictionary mapping feature names to PSI scores
        """
        psi_scores = {}
        
        for feature, window in self.feature_windows.items():
            if len(window) < 100:  # Need minimum samples
                continue
            
            if feature not in self.reference_distributions:
                continue
            
            # Compute current distribution
            current_data = np.array(list(window))
            current_dist = PopulationStabilityIndex.bin_data(current_data, n_bins=10)
            
            # Calculate PSI
            reference_dist = self.reference_distributions[feature]
            psi = PopulationStabilityIndex.calculate_psi(reference_dist, current_dist)
            
            psi_scores[feature] = psi
            
            # Update Prometheus metric
            PSI_GAUGE.labels(feature=feature).set(psi)
            
            # Check threshold and alert
            if psi > self.psi_threshold:
                logger.warning(
                    f"DRIFT ALERT: {feature} has PSI={psi:.4f} "
                    f"(threshold={self.psi_threshold})"
                )
                DRIFT_ALERTS.labels(feature=feature).inc()
        
        return psi_scores
    
    def should_check_drift(self) -> bool:
        """Determine if it's time to check for drift."""
        current_time = time.time()
        if current_time - self.last_check_time >= self.check_interval:
            self.last_check_time = current_time
            return True
        return False

    def run_from_kafka(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str = "drift-monitor"
    ):
        """Monitor drift by consuming from Kafka topic.

        Args:
            bootstrap_servers: Kafka bootstrap servers
            topic: Topic to consume from (predictions or flows)
            group_id: Consumer group ID
        """
        config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'latest',  # Only monitor new data
            'enable.auto.commit': True,
        }

        consumer = Consumer(config)
        consumer.subscribe([topic])

        logger.info(f"Consuming from Kafka topic: {topic}")
        logger.info(f"Window size: {self.window_size}, PSI threshold: {self.psi_threshold}")

        try:
            while True:
                msg = consumer.poll(timeout=1.0)

                if msg is None:
                    # Check for drift periodically even without new messages
                    if self.should_check_drift():
                        psi_scores = self.check_drift()
                        if psi_scores:
                            logger.info(f"Drift check complete. Max PSI: {max(psi_scores.values()):.4f}")
                    continue

                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                # Parse message
                try:
                    value = json.loads(msg.value().decode('utf-8'))

                    # Extract features based on message type
                    if 'predicted_label' in value:
                        # PredictionEvent - skip for now
                        continue
                    else:
                        # NetworkFlowEvent
                        sample = {k: v for k, v in value.items() if k in self.feature_windows}
                        self.add_sample(sample)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")

                # Periodic drift check
                if self.should_check_drift():
                    psi_scores = self.check_drift()

                    if psi_scores:
                        max_psi = max(psi_scores.values())
                        max_feature = max(psi_scores, key=psi_scores.get)

                        logger.info(
                            f"Drift check: {len(psi_scores)} features, "
                            f"max PSI={max_psi:.4f} ({max_feature})"
                        )

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            consumer.close()
            logger.info("Consumer closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI-CTIDS Drift Monitor")
    parser.add_argument(
        '--reference-data',
        required=True,
        help='Path to reference/training data CSV'
    )
    parser.add_argument(
        '--kafka-servers',
        default=settings.KAFKA_BOOTSTRAP_SERVERS,
        help='Kafka bootstrap servers'
    )
    parser.add_argument(
        '--topic',
        default=settings.KAFKA_INPUT_TOPIC,
        help='Kafka topic to monitor'
    )
    parser.add_argument(
        '--window-size',
        type=int,
        default=settings.DRIFT_WINDOW_SIZE,
        help='Rolling window size'
    )
    parser.add_argument(
        '--psi-threshold',
        type=float,
        default=settings.DRIFT_PSI_THRESHOLD,
        help='PSI threshold for alerts'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=settings.DRIFT_CHECK_INTERVAL_SECONDS,
        help='Drift check interval in seconds'
    )
    parser.add_argument(
        '--metrics-port',
        type=int,
        default=8002,
        help='Prometheus metrics port'
    )

    args = parser.parse_args()

    # Start Prometheus metrics server
    start_http_server(args.metrics_port)
    logger.info(f"Prometheus metrics server started on port {args.metrics_port}")

    # Create and run monitor
    monitor = DriftMonitor(
        reference_data_path=args.reference_data,
        window_size=args.window_size,
        psi_threshold=args.psi_threshold,
        check_interval=args.check_interval
    )

    monitor.run_from_kafka(
        bootstrap_servers=args.kafka_servers,
        topic=args.topic
    )


if __name__ == "__main__":
    main()

