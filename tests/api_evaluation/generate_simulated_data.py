"""Generate simulated network flow data for testing.

Creates realistic synthetic network flows for different attack types.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config import settings, SELECTED_FEATURES, LABEL_MAPPING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED = settings.RANDOM_SEED
np.random.seed(SEED)


def generate_benign_flow() -> Dict:
    """Generate a benign network flow."""
    return {
        'Destination_Port': np.random.choice([80, 443, 22, 21, 25, 53]),
        'Flow_Duration': np.random.exponential(5000),
        'Total_Fwd_Packets': np.random.poisson(10),
        'Total_Backward_Packets': np.random.poisson(8),
        'Total_Length_of_Fwd_Packets': np.random.exponential(1500),
        'Total_Length_of_Bwd_Packets': np.random.exponential(1200),
        'Fwd_Packet_Length_Max': np.random.randint(100, 1500),
        'Fwd_Packet_Length_Min': np.random.randint(0, 100),
        'Fwd_Packet_Length_Mean': np.random.uniform(50, 500),
        'Fwd_Packet_Length_Std': np.random.uniform(10, 200),
        'Bwd_Packet_Length_Max': np.random.randint(100, 1500),
        'Bwd_Packet_Length_Min': np.random.randint(0, 100),
        'Bwd_Packet_Length_Mean': np.random.uniform(50, 500),
        'Bwd_Packet_Length_Std': np.random.uniform(10, 200),
        'Flow_Bytes/s': np.random.uniform(100, 10000),
        'Flow_Packets/s': np.random.uniform(1, 100),
        'Flow_IAT_Mean': np.random.uniform(100, 10000),
        'Flow_IAT_Std': np.random.uniform(50, 5000),
        'Flow_IAT_Max': np.random.uniform(1000, 50000),
        'Flow_IAT_Min': np.random.uniform(0, 100),
        'Fwd_IAT_Total': np.random.exponential(10000),
        'Fwd_IAT_Mean': np.random.uniform(100, 5000),
        'Fwd_IAT_Std': np.random.uniform(50, 2000),
        'Fwd_IAT_Max': np.random.uniform(1000, 20000),
        'Fwd_IAT_Min': np.random.uniform(0, 100),
        'Bwd_IAT_Total': np.random.exponential(8000),
        'Bwd_IAT_Mean': np.random.uniform(100, 5000),
        'Bwd_IAT_Std': np.random.uniform(50, 2000),
        'Bwd_IAT_Max': np.random.uniform(1000, 20000),
        'Bwd_IAT_Min': np.random.uniform(0, 100),
        'Fwd_PSH_Flags': np.random.binomial(1, 0.3),
        'Bwd_PSH_Flags': np.random.binomial(1, 0.3),
        'Fwd_URG_Flags': 0,
        'Bwd_URG_Flags': 0,
        'Fwd_Header_Length': np.random.randint(20, 60),
        'Bwd_Header_Length': np.random.randint(20, 60),
        'Fwd_Packets/s': np.random.uniform(1, 50),
        'Bwd_Packets/s': np.random.uniform(1, 40),
        'Min_Packet_Length': np.random.randint(0, 100),
        'Max_Packet_Length': np.random.randint(100, 1500),
        'Packet_Length_Mean': np.random.uniform(50, 500),
        'Packet_Length_Std': np.random.uniform(10, 200),
        'Packet_Length_Variance': np.random.uniform(100, 40000),
        'FIN_Flag_Count': np.random.binomial(1, 0.5),
        'SYN_Flag_Count': np.random.binomial(1, 0.5),
        'RST_Flag_Count': 0,
        'PSH_Flag_Count': np.random.poisson(2),
        'ACK_Flag_Count': np.random.poisson(8),
        'URG_Flag_Count': 0,
        'CWE_Flag_Count': 0,
        'ECE_Flag_Count': 0,
        'Down/Up_Ratio': np.random.uniform(0.5, 2.0),
        'Average_Packet_Size': np.random.uniform(50, 500),
        'Avg_Fwd_Segment_Size': np.random.uniform(50, 500),
        'Avg_Bwd_Segment_Size': np.random.uniform(50, 500),
        'Init_Win_bytes_forward': np.random.randint(1024, 65535),
        'Init_Win_bytes_backward': np.random.randint(1024, 65535),
        'act_data_pkt_fwd': np.random.poisson(5),
        'min_seg_size_forward': np.random.randint(20, 100),
        'Active_Mean': np.random.uniform(100, 10000),
        'Active_Std': np.random.uniform(50, 5000),
        'Active_Max': np.random.uniform(1000, 50000),
        'Active_Min': np.random.uniform(0, 100),
        'Idle_Mean': np.random.uniform(1000, 100000),
        'Label': 'BENIGN'
    }


def generate_dos_flow() -> Dict:
    """Generate a DoS attack flow (high packet rate, low diversity)."""
    flow = generate_benign_flow()
    flow.update({
        'Total_Fwd_Packets': np.random.poisson(1000),
        'Total_Backward_Packets': np.random.poisson(10),
        'Flow_Packets/s': np.random.uniform(1000, 10000),
        'Fwd_Packets/s': np.random.uniform(1000, 10000),
        'Bwd_Packets/s': np.random.uniform(0, 10),
        'Down/Up_Ratio': np.random.uniform(0.001, 0.1),
        'SYN_Flag_Count': np.random.poisson(50),
        'Label': 'DoS Hulk'
    })
    return flow


def generate_portscan_flow() -> Dict:
    """Generate a port scan flow (many flows, minimal data)."""
    flow = generate_benign_flow()
    flow.update({
        'Destination_Port': np.random.randint(1, 65535),
        'Flow_Duration': np.random.uniform(0, 1000),
        'Total_Fwd_Packets': np.random.poisson(2),
        'Total_Backward_Packets': 0,
        'Flow_Packets/s': np.random.uniform(10, 100),
        'SYN_Flag_Count': 1,
        'ACK_Flag_Count': 0,
        'Label': 'PortScan'
    })
    return flow


def generate_ddos_flow() -> Dict:
    """Generate a DDoS attack flow."""
    flow = generate_benign_flow()
    flow.update({
        'Total_Fwd_Packets': np.random.poisson(500),
        'Flow_Packets/s': np.random.uniform(500, 5000),
        'Fwd_Packets/s': np.random.uniform(500, 5000),
        'Label': 'DDoS'
    })
    return flow


FLOW_GENERATORS = {
    'BENIGN': generate_benign_flow,
    'DoS Hulk': generate_dos_flow,
    'PortScan': generate_portscan_flow,
    'DDoS': generate_ddos_flow,
}


def generate_simulated_dataset(n_samples: int = 1000, output_path: str = None) -> pd.DataFrame:
    """Generate a simulated dataset with various attack types.

    Args:
        n_samples: Total number of samples to generate
        output_path: Optional path to save CSV

    Returns:
        DataFrame with simulated flows
    """
    logger.info(f"Generating {n_samples} simulated network flows")

    # Generate samples for each type
    flows = []
    samples_per_type = n_samples // len(FLOW_GENERATORS)

    for label, generator in FLOW_GENERATORS.items():
        logger.info(f"Generating {samples_per_type} flows for {label}")
        for _ in range(samples_per_type):
            flows.append(generator())

    df = pd.DataFrame(flows)

    # Shuffle
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    logger.info(f"Generated dataset shape: {df.shape}")
    logger.info(f"Label distribution:\n{df['Label'].value_counts()}")

    if output_path:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved simulated dataset to {output_path}")

    return df


def main():
    parser = argparse.ArgumentParser(description="Generate simulated network flow data")
    parser.add_argument("--n-samples", type=int, default=1000,
                       help="Number of samples to generate")
    parser.add_argument("--output", type=str, default="./tests/api_evaluation/data/simulated_flows.csv",
                       help="Output CSV path")

    args = parser.parse_args()

    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    generate_simulated_dataset(n_samples=args.n_samples, output_path=args.output)

    logger.info("Simulated data generation complete!")


if __name__ == "__main__":
    main()

