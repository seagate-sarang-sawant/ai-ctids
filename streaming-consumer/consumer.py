"""Kafka consumer for streaming network flow threat detection.

Consumes network flow events from Kafka, scores them, and publishes predictions.
"""

import json
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from prometheus_client import Counter, Histogram, start_http_server

sys.path.append(str(Path(__file__).parent.parent))
from shared.schemas import NetworkFlowEvent, PredictionEvent
from shared.config import settings
from inference_api.predictor import ThreatPredictor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
MESSAGES_CONSUMED = Counter('kafka_messages_consumed_total', 'Total messages consumed', ['topic'])
MESSAGES_PRODUCED = Counter('kafka_messages_produced_total', 'Total messages produced', ['topic'])
MESSAGE_PROCESSING_TIME = Histogram('message_processing_seconds', 'Message processing time')
ERRORS_COUNTER = Counter('kafka_consumer_errors_total', 'Total processing errors', ['error_type'])


class ThreatDetectionConsumer:
    """Kafka consumer for real-time threat detection."""
    
    def __init__(
        self,
        input_topic: str,
        output_topic: str,
        bootstrap_servers: str,
        group_id: str,
        model_path: Optional[str] = None
    ):
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.running = True
        
        # Initialize predictor
        logger.info("Loading model...")
        self.predictor = ThreatPredictor(model_path)
        logger.info("Model loaded successfully")
        
        # Configure consumer
        self.consumer_config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': settings.KAFKA_AUTO_OFFSET_RESET,
            'enable.auto.commit': True,
            'auto.commit.interval.ms': 5000,
        }
        
        # Configure producer
        self.producer_config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': f'{group_id}-producer',
        }
        
        self.consumer = Consumer(self.consumer_config)
        self.producer = Producer(self.producer_config)
        
        # Subscribe to input topic
        self.consumer.subscribe([input_topic])
        logger.info(f"Subscribed to topic: {input_topic}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        """Gracefully shutdown consumer."""
        logger.info("Shutdown signal received")
        self.running = False
    
    def delivery_report(self, err, msg):
        """Callback for producer delivery reports."""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
            ERRORS_COUNTER.labels(error_type='delivery_failure').inc()
        else:
            MESSAGES_PRODUCED.labels(topic=msg.topic()).inc()
    
    def process_message(self, message):
        """Process a single message."""
        try:
            with MESSAGE_PROCESSING_TIME.time():
                # Parse message
                value = json.loads(message.value().decode('utf-8'))
                
                # Create NetworkFlowEvent
                flow_event = NetworkFlowEvent(**value)
                
                # Make prediction
                prediction = self.predictor.predict_single(flow_event)
                
                # Publish prediction
                prediction_json = prediction.json()
                self.producer.produce(
                    self.output_topic,
                    key=message.key(),
                    value=prediction_json.encode('utf-8'),
                    callback=self.delivery_report
                )
                
                # Flush to ensure delivery
                self.producer.poll(0)
                
                logger.debug(
                    f"Processed flow: {flow_event.correlation_id} -> "
                    f"Prediction: {prediction.predicted_label} "
                    f"(confidence: {prediction.confidence:.3f})"
                )
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
            ERRORS_COUNTER.labels(error_type='json_decode').inc()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ERRORS_COUNTER.labels(error_type='processing').inc()
    
    def run(self):
        """Main consumer loop."""
        logger.info("Starting consumer loop")
        
        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition: {msg.topic()}[{msg.partition()}]")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        ERRORS_COUNTER.labels(error_type='kafka_error').inc()
                    continue
                
                # Process message
                MESSAGES_CONSUMED.labels(topic=msg.topic()).inc()
                self.process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            ERRORS_COUNTER.labels(error_type='unexpected').inc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up resources...")
        
        # Flush producer
        logger.info("Flushing producer...")
        self.producer.flush()
        
        # Close consumer
        logger.info("Closing consumer...")
        self.consumer.close()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-CTIDS Streaming Consumer")
    parser.add_argument(
        '--input-topic',
        default=settings.KAFKA_INPUT_TOPIC,
        help='Input Kafka topic'
    )
    parser.add_argument(
        '--output-topic',
        default=settings.KAFKA_OUTPUT_TOPIC,
        help='Output Kafka topic'
    )
    parser.add_argument(
        '--bootstrap-servers',
        default=settings.KAFKA_BOOTSTRAP_SERVERS,
        help='Kafka bootstrap servers'
    )
    parser.add_argument(
        '--group-id',
        default=settings.KAFKA_CONSUMER_GROUP,
        help='Consumer group ID'
    )
    parser.add_argument(
        '--model-path',
        default=None,
        help='Path to model file'
    )
    parser.add_argument(
        '--metrics-port',
        type=int,
        default=8001,
        help='Prometheus metrics port'
    )
    
    args = parser.parse_args()
    
    # Start Prometheus metrics server
    start_http_server(args.metrics_port)
    logger.info(f"Prometheus metrics server started on port {args.metrics_port}")
    
    # Create and run consumer
    consumer = ThreatDetectionConsumer(
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        bootstrap_servers=args.bootstrap_servers,
        group_id=args.group_id,
        model_path=args.model_path
    )
    
    consumer.run()


if __name__ == "__main__":
    main()
