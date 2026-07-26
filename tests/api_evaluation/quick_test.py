"""Quick API test with a few sample predictions.

Use this for quick validation that the API is working correctly.
"""

import sys
import logging
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config import SELECTED_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_health_endpoints(api_url: str = "http://localhost:8000"):
    """Test health and readiness endpoints."""
    logger.info("Testing health endpoints...")
    
    # Health check
    try:
        response = requests.get(f"{api_url}/healthz", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Health check passed")
        else:
            logger.error(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return False
    
    # Readiness check
    try:
        response = requests.get(f"{api_url}/readyz", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Readiness check passed")
            logger.info(f"  Model info: {response.json()}")
        else:
            logger.error(f"✗ Readiness check failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"✗ Readiness check failed: {e}")
        return False
    
    return True


def create_sample_benign_flow():
    """Create a sample benign network flow."""
    return {
        'destination_port': 80,
        'flow_duration': 1234.5,
        'total_fwd_packets': 10.0,
        'total_backward_packets': 8.0,
        'total_length_of_fwd_packets': 1500.0,
        'total_length_of_bwd_packets': 1200.0,
        'fwd_packet_length_max': 500.0,
        'fwd_packet_length_min': 50.0,
        'fwd_packet_length_mean': 150.0,
        'fwd_packet_length_std': 75.0,
        'bwd_packet_length_max': 400.0,
        'bwd_packet_length_min': 40.0,
        'bwd_packet_length_mean': 150.0,
        'bwd_packet_length_std': 60.0,
        'flow_bytes_s': 1000.0,
        'flow_packets_s': 10.0,
        'flow_iat_mean': 100.0,
        'flow_iat_std': 50.0,
        'flow_iat_max': 500.0,
        'flow_iat_min': 10.0,
        'fwd_iat_total': 1000.0,
        'fwd_iat_mean': 100.0,
        'fwd_iat_std': 50.0,
        'fwd_iat_max': 300.0,
        'fwd_iat_min': 10.0,
        'bwd_iat_total': 800.0,
        'bwd_iat_mean': 100.0,
        'bwd_iat_std': 40.0,
        'bwd_iat_max': 250.0,
        'bwd_iat_min': 15.0,
        'fwd_psh_flags': 1,
        'bwd_psh_flags': 1,
        'fwd_urg_flags': 0,
        'bwd_urg_flags': 0,
        'fwd_header_length': 40.0,
        'bwd_header_length': 40.0,
        'fwd_packets_s': 5.0,
        'bwd_packets_s': 4.0,
        'min_packet_length': 40.0,
        'max_packet_length': 500.0,
        'packet_length_mean': 150.0,
        'packet_length_std': 75.0,
        'packet_length_variance': 5625.0,
        'fin_flag_count': 1,
        'syn_flag_count': 1,
        'rst_flag_count': 0,
        'psh_flag_count': 2,
        'ack_flag_count': 8,
        'urg_flag_count': 0,
        'cwe_flag_count': 0,
        'ece_flag_count': 0,
        'down_up_ratio': 0.8,
        'average_packet_size': 150.0,
        'avg_fwd_segment_size': 150.0,
        'avg_bwd_segment_size': 150.0,
        'init_win_bytes_forward': 8192,
        'init_win_bytes_backward': 8192,
        'act_data_pkt_fwd': 5,
        'min_seg_size_forward': 20,
        'active_mean': 1000.0,
        'active_std': 200.0,
        'active_max': 2000.0,
        'active_min': 100.0,
        'idle_mean': 5000.0
    }


def test_single_prediction(api_url: str = "http://localhost:8000"):
    """Test single prediction endpoint."""
    logger.info("\nTesting single prediction endpoint...")

    flow = create_sample_benign_flow()

    try:
        response = requests.post(
            f"{api_url}/predict",
            json=flow,
            timeout=10
        )

        if response.status_code != 200:
            logger.error(f"✗ Single prediction failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return False

        prediction = response.json()

        logger.info("✓ Single prediction successful")
        logger.info(f"  Predicted label: {prediction['predicted_label']}")
        logger.info(f"  Confidence: {prediction['confidence']:.4f}")
        logger.info(f"  Inference time: {prediction['inference_time_ms']:.2f}ms")
        return True
    except Exception as e:
        logger.error(f"✗ Single prediction failed: {e}")
        return False


def test_batch_prediction(api_url: str = "http://localhost:8000"):
    """Test batch prediction endpoint."""
    logger.info("\nTesting batch prediction endpoint...")
    
    # Create 5 sample flows
    flows = [create_sample_benign_flow() for _ in range(5)]
    
    try:
        response = requests.post(
            f"{api_url}/predict/batch",
            json={"flows": flows},
            timeout=30
        )
        response.raise_for_status()
        batch_response = response.json()
        
        logger.info("✓ Batch prediction successful")
        logger.info(f"  Total predictions: {batch_response['total_count']}")
        logger.info(f"  Total time: {batch_response['total_inference_time_ms']:.2f}ms")
        logger.info(f"  Average time per sample: {batch_response['average_inference_time_ms']:.2f}ms")
        
        # Show first prediction
        if batch_response['predictions']:
            first_pred = batch_response['predictions'][0]
            logger.info(f"  First prediction: {first_pred['predicted_label']} "
                       f"(confidence: {first_pred['confidence']:.4f})")
        
        return True
    except Exception as e:
        logger.error(f"✗ Batch prediction failed: {e}")
        return False


def main():
    api_url = "http://localhost:8000"
    
    logger.info("="*80)
    logger.info("AI-CTIDS API QUICK TEST")
    logger.info("="*80)
    
    # Test health endpoints
    if not test_health_endpoints(api_url):
        logger.error("\nAPI is not ready. Please start the API with trained models.")
        sys.exit(1)
    
    # Test single prediction
    if not test_single_prediction(api_url):
        logger.error("\nSingle prediction test failed")
        sys.exit(1)
    
    # Test batch prediction
    if not test_batch_prediction(api_url):
        logger.error("\nBatch prediction test failed")
        sys.exit(1)
    
    logger.info("\n" + "="*80)
    logger.info("ALL TESTS PASSED! ✓")
    logger.info("="*80)
    logger.info("\nThe API is working correctly. You can now:")
    logger.info("  1. Run full evaluation: python3 run_all_tests.py")
    logger.info("  2. Test with real data: python3 test_api.py --data-path ./data/validation_small.csv")


if __name__ == "__main__":
    main()
