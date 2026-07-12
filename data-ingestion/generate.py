"""Data ingestion for CICIDS2017 network flows.

Supports batch and streaming modes with synthetic drift injection.
"""

import argparse
import json
import logging
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Iterator

import pandas as pd
import numpy as np
from confluent_kafka import Producer

import sys
sys.path.append(str(Path(__file__).parent.parent))
from shared.schemas import NetworkFlowEvent, ThreatLabel
from shared.config import settings, SELECTED_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NetworkFlowGenerator:
    """Generate network flow events from CICIDS2017 dataset."""
    
    def __init__(
        self,
        data_path: str,
        drift_mode: Optional[str] = None,
        drift_factor: float = 2.0
    ):
        self.data_path = data_path
        self.drift_mode = drift_mode
        self.drift_factor = drift_factor
        
        logger.info(f"Loading data from {data_path}")
        self.df = pd.read_csv(data_path)
        
        # Standardize column names
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.replace(" ", "_", regex=False)
        )
        
        logger.info(f"Loaded {len(self.df):,} network flows")
        
        if drift_mode:
            logger.info(f"Drift injection enabled: {drift_mode} with factor {drift_factor}")
    
    def inject_drift(self, row: pd.Series) -> pd.Series:
        """Inject synthetic drift into network flow features.
        
        Args:
            row: Original row
        
        Returns:
            Row with drift injected
        """
        if self.drift_mode is None:
            return row
        
        row = row.copy()
        
        if self.drift_mode == "flow_duration":
            # Increase flow duration
            row['Flow_Duration'] *= self.drift_factor
        
        elif self.drift_mode == "packet_size":
            # Increase packet sizes
            for col in ['Fwd_Packet_Length_Mean', 'Bwd_Packet_Length_Mean', 'Average_Packet_Size']:
                if col in row:
                    row[col] *= self.drift_factor
        
        elif self.drift_mode == "port_shift":
            # Shift destination port distribution
            if 'Destination_Port' in row:
                row['Destination_Port'] = int(row['Destination_Port'] * 1.5) % 65536
        
        elif self.drift_mode == "benign_to_attack":
            # Simulate benign traffic appearing more like attacks
            if row.get('Label') == 'BENIGN':
                row['Flow_Packets/s'] *= self.drift_factor
                row['SYN_Flag_Count'] = min(row.get('SYN_Flag_Count', 0) + 5, 100)
        
        return row
    
    def row_to_event(self, row: pd.Series, apply_drift: bool = True) -> NetworkFlowEvent:
        """Convert dataframe row to NetworkFlowEvent.
        
        Args:
            row: Dataframe row
            apply_drift: Whether to apply drift injection
        
        Returns:
            NetworkFlowEvent instance
        """
        if apply_drift:
            row = self.inject_drift(row)
        
        # Extract label if present
        true_label = None
        if 'Label' in row:
            try:
                true_label = ThreatLabel(row['Label'])
            except ValueError:
                logger.warning(f"Unknown label: {row['Label']}")
        
        # Create event with available features
        event_data = {
            'correlation_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow(),
        }
        
        # Map DataFrame columns to NetworkFlowEvent fields
        for col in row.index:
            if col == 'Label':
                continue
            
            # Convert column name to snake_case field name
            field_name = col.lower()
            value = row[col]
            
            # Handle NaN/None values
            if pd.isna(value):
                value = 0.0
            
            event_data[field_name] = float(value) if isinstance(value, (int, float)) else value
        
        if true_label:
            event_data['true_label'] = true_label
        
        try:
            event = NetworkFlowEvent(**event_data)
            return event
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            logger.error(f"Event data keys: {event_data.keys()}")
            raise
    
    def generate_batch(self, n_samples: int = 100, apply_drift: bool = False) -> list[NetworkFlowEvent]:
        """Generate batch of network flow events.
        
        Args:
            n_samples: Number of samples to generate
            apply_drift: Whether to apply drift injection
        
        Returns:
            List of NetworkFlowEvent instances
        """
        logger.info(f"Generating batch of {n_samples} samples")
        
        # Sample from dataset
        sample_df = self.df.sample(n=min(n_samples, len(self.df)), replace=False)
        
        events = []
        for _, row in sample_df.iterrows():
            try:
                event = self.row_to_event(row, apply_drift=apply_drift)
                events.append(event)
            except Exception as e:
                logger.error(f"Skipping row due to error: {e}")
        
        logger.info(f"Generated {len(events)} events")
        return events
    
    def generate_stream(
        self,
        rate_per_second: float = 10.0,
        apply_drift: bool = False,
        max_events: Optional[int] = None
    ) -> Iterator[NetworkFlowEvent]:
        """Generate stream of network flow events.
        
        Args:
            rate_per_second: Number of events to generate per second
            apply_drift: Whether to apply drift injection
            max_events: Maximum number of events (None for infinite)
        
        Yields:
            NetworkFlowEvent instances
        """
        logger.info(f"Starting stream generation at {rate_per_second} events/sec")
        
        interval = 1.0 / rate_per_second
        count = 0
        
        while True:
            if max_events and count >= max_events:
                break
            
            # Sample random row
            row = self.df.sample(n=1).iloc[0]

            try:
                event = self.row_to_event(row, apply_drift=apply_drift)
                yield event
                count += 1

                # Sleep to maintain rate
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error generating event: {e}")


class KafkaFlowProducer:
    """Produce network flows to Kafka."""

    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic

        config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'ai-ctids-data-ingestion',
        }

        self.producer = Producer(config)
        logger.info(f"Kafka producer initialized for topic: {topic}")

    def delivery_report(self, err, msg):
        """Callback for delivery reports."""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def produce_event(self, event: NetworkFlowEvent):
        """Produce single event to Kafka."""
        try:
            # Serialize to JSON
            value = event.json().encode('utf-8')
            key = event.correlation_id.encode('utf-8') if event.correlation_id else None

            # Produce
            self.producer.produce(
                self.topic,
                key=key,
                value=value,
                callback=self.delivery_report
            )

            # Trigger delivery callbacks
            self.producer.poll(0)

        except Exception as e:
            logger.error(f"Failed to produce event: {e}")

    def close(self):
        """Flush and close producer."""
        logger.info("Flushing producer...")
        self.producer.flush()
        logger.info("Producer closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI-CTIDS Data Ingestion")
    parser.add_argument('--data-path', type=str, required=True, help='Path to CICIDS2017 CSV')
    parser.add_argument('--mode', choices=['batch', 'stream'], default='batch', help='Generation mode')
    parser.add_argument('--output', type=str, help='Output file for batch mode')

    # Streaming options
    parser.add_argument('--kafka-servers', default=settings.KAFKA_BOOTSTRAP_SERVERS,
                       help='Kafka bootstrap servers')
    parser.add_argument('--topic', default=settings.KAFKA_INPUT_TOPIC,
                       help='Kafka topic')
    parser.add_argument('--rate', type=float, default=10.0,
                       help='Events per second (stream mode)')
    parser.add_argument('--max-events', type=int, help='Maximum events (stream mode)')

    # Batch options
    parser.add_argument('--n-samples', type=int, default=1000,
                       help='Number of samples (batch mode)')

    # Drift options
    parser.add_argument('--drift', choices=['flow_duration', 'packet_size', 'port_shift', 'benign_to_attack'],
                       help='Drift injection mode')
    parser.add_argument('--drift-factor', type=float, default=2.0,
                       help='Drift multiplication factor')

    args = parser.parse_args()

    # Create generator
    generator = NetworkFlowGenerator(
        data_path=args.data_path,
        drift_mode=args.drift,
        drift_factor=args.drift_factor
    )

    if args.mode == 'batch':
        # Generate batch
        events = generator.generate_batch(
            n_samples=args.n_samples,
            apply_drift=args.drift is not None
        )

        # Save to file
        if args.output:
            logger.info(f"Saving {len(events)} events to {args.output}")
            with open(args.output, 'w') as f:
                for event in events:
                    f.write(event.json() + '\n')
        else:
            # Print to stdout
            for event in events:
                print(event.json())

    elif args.mode == 'stream':
        # Create Kafka producer
        producer = KafkaFlowProducer(
            bootstrap_servers=args.kafka_servers,
            topic=args.topic
        )

        try:
            # Generate and publish stream
            for event in generator.generate_stream(
                rate_per_second=args.rate,
                apply_drift=args.drift is not None,
                max_events=args.max_events
            ):
                producer.produce_event(event)
                logger.info(
                    f"Produced event {event.correlation_id}: "
                    f"{event.true_label if event.true_label else 'Unknown'}"
                )
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            producer.close()

    logger.info("Data generation complete")


if __name__ == "__main__":
    main()

