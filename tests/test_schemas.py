"""Tests for shared schemas."""

import pytest
from datetime import datetime
from shared.schemas import NetworkFlowEvent, PredictionEvent, ThreatLabel


def test_network_flow_event_creation():
    """Test NetworkFlowEvent can be created with valid data."""
    event = NetworkFlowEvent(
        destination_port=80,
        flow_duration=1234.5,
        total_fwd_packets=10.0,
        total_backward_packets=8.0,
        total_length_of_fwd_packets=500.0,
        total_length_of_bwd_packets=400.0,
        fwd_packet_length_max=100.0,
        fwd_packet_length_min=20.0,
        fwd_packet_length_mean=50.0,
        fwd_packet_length_std=15.5,
        bwd_packet_length_max=80.0,
        bwd_packet_length_min=10.0,
        bwd_packet_length_mean=40.0,
        bwd_packet_length_std=12.0,
        flow_bytes_s=10000.0,
        flow_packets_s=100.0,
        flow_iat_mean=50.0,
        flow_iat_std=10.0,
        flow_iat_max=100.0,
        flow_iat_min=10.0,
    )
    
    assert event.destination_port == 80
    assert event.flow_duration == 1234.5
    assert event.timestamp is not None


def test_network_flow_event_port_validation():
    """Test port number validation."""
    with pytest.raises(ValueError):
        NetworkFlowEvent(
            destination_port=70000,  # Invalid port
            flow_duration=1000.0,
            total_fwd_packets=10.0,
            total_backward_packets=8.0,
            total_length_of_fwd_packets=500.0,
            total_length_of_bwd_packets=400.0,
            fwd_packet_length_max=100.0,
            fwd_packet_length_min=20.0,
            fwd_packet_length_mean=50.0,
            fwd_packet_length_std=15.5,
            bwd_packet_length_max=80.0,
            bwd_packet_length_min=10.0,
            bwd_packet_length_mean=40.0,
            bwd_packet_length_std=12.0,
            flow_bytes_s=10000.0,
            flow_packets_s=100.0,
            flow_iat_mean=50.0,
            flow_iat_std=10.0,
            flow_iat_max=100.0,
            flow_iat_min=10.0,
        )


def test_prediction_event_creation():
    """Test PredictionEvent creation."""
    prediction = PredictionEvent(
        request_id="test-123",
        predicted_label=ThreatLabel.BENIGN,
        predicted_label_encoded=0,
        confidence=0.95,
        probabilities={
            "BENIGN": 0.95,
            "DoS Hulk": 0.03,
            "PortScan": 0.02
        },
        model_name="xgboost",
        model_version="1.0.0",
        inference_time_ms=12.5
    )
    
    assert prediction.predicted_label == ThreatLabel.BENIGN
    assert prediction.confidence == 0.95
    assert prediction.model_name == "xgboost"


def test_prediction_probabilities_validation():
    """Test probabilities sum to 1.0."""
    with pytest.raises(ValueError):
        PredictionEvent(
            request_id="test-123",
            predicted_label=ThreatLabel.BENIGN,
            predicted_label_encoded=0,
            confidence=0.95,
            probabilities={
                "BENIGN": 0.5,  # Doesn't sum to 1.0
                "DoS Hulk": 0.3,
            },
            model_name="xgboost",
            model_version="1.0.0",
            inference_time_ms=12.5
        )


def test_network_flow_to_feature_dict():
    """Test conversion to feature dictionary."""
    event = NetworkFlowEvent(
        destination_port=443,
        flow_duration=5000.0,
        total_fwd_packets=15.0,
        total_backward_packets=12.0,
        total_length_of_fwd_packets=750.0,
        total_length_of_bwd_packets=600.0,
        fwd_packet_length_max=150.0,
        fwd_packet_length_min=30.0,
        fwd_packet_length_mean=60.0,
        fwd_packet_length_std=20.0,
        bwd_packet_length_max=100.0,
        bwd_packet_length_min=15.0,
        bwd_packet_length_mean=50.0,
        bwd_packet_length_std=15.0,
        flow_bytes_s=15000.0,
        flow_packets_s=150.0,
        flow_iat_mean=60.0,
        flow_iat_std=15.0,
        flow_iat_max=120.0,
        flow_iat_min=20.0,
    )
    
    features = event.to_feature_dict()
    
    assert 'destination_port' in features
    assert features['destination_port'] == 443
    assert 'timestamp' not in features
    assert 'correlation_id' not in features


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
