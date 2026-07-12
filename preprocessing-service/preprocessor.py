"""Streaming preprocessing service that consumes raw flows and publishes cleaned flows.

This service sits between data-ingestion and inference services to:
1. Validate data quality
2. Handle missing values
3. Apply feature selection
4. Optionally scale features
"""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

from confluent_kafka import Consumer, Producer, KafkaError
from prometheus_client import Counter, Histogram, start_http_server

sys.path.append(str(Path(__file__).parent.parent))
from shared.schemas import NetworkFlowEvent
from shared.config import settings
from shared.feature_engineering import FeatureEngineer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
FLOWS_PROCESSED = Counter('preprocessing_flows_processed_total', 'Total flows processed')
FLOWS_VALID = Counter('preprocessing_flows_valid_total', 'Valid flows after preprocessing')
FLOWS_INVALID = Counter('preprocessing_flows_invalid_total', 'Invalid flows rejected', ['reason'])
PROCESSING_TIME = Histogram('preprocessing_duration_seconds', 'Time to preprocess flow')


class StreamingPreprocessor:
    """Preprocessing service for real-time network flows."""
    
    def __init__(
        self,
        input_topic: str,
        output_topic: str,
        bootstrap_servers: str,
        group_id: str = "preprocessing-service",
        artifacts_path: Optional[str] = None
    ):
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.running = True
        
        # Load preprocessing artifacts
        self.feature_engineer = FeatureEngineer()
        if artifacts_path:
            logger.info(f"Loading preprocessing artifacts from {artifacts_path}")
            self.feature_engineer.load_artifacts(artifacts_path)
        
        # Configure consumer
        self.consumer_config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
        }
        
        # Configure producer
        self.producer_config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': f'{group_id}-producer',
        }
        
        self.consumer = Consumer(self.consumer_config)
        self.producer = Producer(self.producer_config)
        
        self.consumer.subscribe([input_topic])
        logger.info(f"Preprocessing service started: {input_topic} → {output_topic}")
    
    def validate_flow(self, flow: NetworkFlowEvent) -> tuple[bool, Optional[str]]:
        """Validate network flow data quality.
        
        Returns:
            (is_valid, error_reason)
        """
        # Check for required fields
        required_fields = [
            'destination_port', 'flow_duration', 'total_fwd_packets',
            'total_backward_packets'
        ]
        
        for field in required_fields:
            value = getattr(flow, field, None)
            if value is None:
                return False, f"missing_{field}"
        
        # Check for invalid values
        if flow.destination_port < 0 or flow.destination_port > 65535:
            return False, "invalid_port"
        
        if flow.flow_duration < 0:
            return False, "negative_duration"
        
        # Check for extreme outliers (potential data corruption)
        if flow.flow_duration > 1e9:  # > 31 years in microseconds
            return False, "extreme_duration"
        
        return True, None
    
    def preprocess_flow(self, flow: NetworkFlowEvent) -> Optional[NetworkFlowEvent]:
        """Preprocess a single network flow.
        
        Returns:
            Preprocessed flow or None if invalid
        """
        with PROCESSING_TIME.time():
            # Validate
            is_valid, error_reason = self.validate_flow(flow)
            if not is_valid:
                FLOWS_INVALID.labels(reason=error_reason).inc()
                logger.warning(f"Invalid flow rejected: {error_reason}")
                return None
            
            # Convert to feature dict
            features = flow.to_feature_dict()
            
            # Handle missing values (if feature engineer is configured)
            if self.feature_engineer.median_values:
                for feature, value in features.items():
                    if value is None and feature in self.feature_engineer.median_values:
                        features[feature] = self.feature_engineer.median_values[feature]
            
            # Create cleaned flow event
            cleaned_flow = NetworkFlowEvent(**{
                **features,
                'correlation_id': flow.correlation_id,
                'timestamp': flow.timestamp,
                'true_label': flow.true_label
            })
            
            FLOWS_VALID.inc()
            return cleaned_flow
    
    def delivery_report(self, err, msg):
        """Callback for producer delivery reports."""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
    
    def process_message(self, message):
        """Process a single Kafka message."""
        try:
            # Parse raw flow
            value = json.loads(message.value().decode('utf-8'))
            raw_flow = NetworkFlowEvent(**value)
            
            FLOWS_PROCESSED.inc()
            
            # Preprocess
            cleaned_flow = self.preprocess_flow(raw_flow)
            
            if cleaned_flow:
                # Publish to output topic
                self.producer.produce(
                    self.output_topic,
                    key=message.key(),
                    value=cleaned_flow.json().encode('utf-8'),
                    callback=self.delivery_report
                )
                self.producer.poll(0)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            FLOWS_INVALID.labels(reason='processing_error').inc()
    
    def run(self):
        """Main processing loop."""
        logger.info("Starting preprocessing loop")
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                self.process_message(msg)
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("Flushing producer...")
        self.producer.flush()
        logger.info("Closing consumer...")
        self.consumer.close()
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-CTIDS Preprocessing Service")
    parser.add_argument('--input-topic', default='network-flows-raw')
    parser.add_argument('--output-topic', default='network-flows-processed')
    parser.add_argument('--bootstrap-servers', default=settings.KAFKA_BOOTSTRAP_SERVERS)
    parser.add_argument('--artifacts-path', default=str(settings.MODELS_DIR))
    parser.add_argument('--metrics-port', type=int, default=8003)
    
    args = parser.parse_args()
    
    # Start metrics server
    start_http_server(args.metrics_port)
    logger.info(f"Metrics server started on port {args.metrics_port}")
    
    # Run preprocessor
    preprocessor = StreamingPreprocessor(
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        bootstrap_servers=args.bootstrap_servers,
        artifacts_path=args.artifacts_path
    )
    
    preprocessor.run()


if __name__ == "__main__":
    main()
