"""Pydantic schemas for network flow events and predictions.

Based on CICIDS2017 dataset schema from the notebook.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class BaseMessage(BaseModel):
    """Base message for all events with timestamp and correlation ID."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreatLabel(str, Enum):
    """Threat classification labels from CICIDS2017."""
    
    BENIGN = "BENIGN"
    DOS_HULK = "DoS Hulk"
    PORT_SCAN = "PortScan"
    DDOS = "DDoS"
    DOS_GOLDENEYE = "DoS GoldenEye"
    FTP_PATATOR = "FTP-Patator"
    SSH_PATATOR = "SSH-Patator"
    DOS_SLOWLORIS = "DoS slowloris"
    DOS_SLOWHTTPTEST = "DoS Slowhttptest"
    BOT = "Bot"
    WEB_ATTACK_BRUTE_FORCE = "Web Attack_Brute Force"
    WEB_ATTACK_XSS = "Web Attack_XSS"
    INFILTRATION = "Infiltration"
    WEB_ATTACK_SQL_INJECTION = "Web Attack_Sql Injection"
    HEARTBLEED = "Heartbleed"


class NetworkFlowEvent(BaseMessage):
    """Network flow event representing a single traffic flow.
    
    Features extracted from CICIDS2017 dataset.
    """
    
    # Flow identifiers
    destination_port: int = Field(..., ge=0, le=65535)
    
    # Flow characteristics
    flow_duration: float = Field(..., ge=0)
    total_fwd_packets: float = Field(..., ge=0)
    total_backward_packets: float = Field(..., ge=0)
    total_length_of_fwd_packets: float = Field(..., ge=0)
    total_length_of_bwd_packets: float = Field(..., ge=0)
    
    # Packet statistics
    fwd_packet_length_max: float = Field(..., ge=0)
    fwd_packet_length_min: float = Field(..., ge=0)
    fwd_packet_length_mean: float = Field(..., ge=0)
    fwd_packet_length_std: float = Field(..., ge=0)
    bwd_packet_length_max: float = Field(..., ge=0)
    bwd_packet_length_min: float = Field(..., ge=0)
    bwd_packet_length_mean: float = Field(..., ge=0)
    bwd_packet_length_std: float = Field(..., ge=0)
    
    # Flow metrics
    flow_bytes_s: float
    flow_packets_s: float
    flow_iat_mean: float
    flow_iat_std: float
    flow_iat_max: float
    flow_iat_min: float
    
    # Additional features (63 total selected features)
    # Add remaining features as needed
    
    # Optional ground truth for evaluation
    true_label: Optional[ThreatLabel] = None
    
    @validator('flow_duration')
    def validate_duration(cls, v):
        """Ensure flow duration is reasonable."""
        if v > 1e9:  # More than ~31 years in microseconds
            raise ValueError("Flow duration exceeds reasonable bounds")
        return v
    
    def to_feature_dict(self) -> Dict[str, float]:
        """Convert to feature dictionary for model input."""
        exclude_fields = {'timestamp', 'correlation_id', 'true_label'}
        return {
            k: v for k, v in self.dict().items() 
            if k not in exclude_fields and v is not None
        }


class PredictionEvent(BaseMessage):
    """Prediction result from the model."""
    
    # Input reference
    request_id: str
    
    # Prediction
    predicted_label: ThreatLabel
    predicted_label_encoded: int
    
    # Confidence scores
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: Dict[str, float]
    
    # Model metadata
    model_name: str
    model_version: str
    
    # Inference metrics
    inference_time_ms: float
    
    @validator('probabilities')
    def validate_probabilities(cls, v):
        """Ensure probabilities sum to approximately 1.0."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Probabilities must sum to 1.0, got {total}")
        return v


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions."""
    
    flows: List[NetworkFlowEvent]
    
    @validator('flows')
    def validate_batch_size(cls, v):
        """Ensure batch size is reasonable."""
        if len(v) > 1000:
            raise ValueError("Batch size exceeds maximum of 1000")
        if len(v) == 0:
            raise ValueError("Batch must contain at least one flow")
        return v


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions."""
    
    predictions: List[PredictionEvent]
    total_count: int
    total_inference_time_ms: float
    average_inference_time_ms: float
