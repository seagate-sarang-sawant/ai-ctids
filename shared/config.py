"""Configuration management for AI-CTIDS pipeline."""

import os
from pathlib import Path
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "ai-ctids"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # Model
    MODEL_NAME: str = "xgboost"
    MODEL_VERSION: str = "latest"
    MODEL_PATH: Optional[Path] = None
    SCALER_PATH: Optional[Path] = None
    LABEL_ENCODER_PATH: Optional[Path] = None
    SELECTED_FEATURES_PATH: Optional[Path] = None
    
    # Training
    RANDOM_SEED: int = 42
    TRAIN_SPLIT: float = 0.7
    VAL_SPLIT: float = 0.15
    TEST_SPLIT: float = 0.15
    
    # Weights & Biases
    WANDB_PROJECT: str = "ai-ctids"
    WANDB_ENTITY: Optional[str] = None
    WANDB_API_KEY: Optional[str] = None
    
    # API Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_INPUT_TOPIC: str = "network-flows"
    KAFKA_OUTPUT_TOPIC: str = "threat-predictions"
    KAFKA_CONSUMER_GROUP: str = "ai-ctids-consumer"
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    METRICS_ENABLED: bool = True
    
    # Drift Detection
    DRIFT_WINDOW_SIZE: int = 10000
    DRIFT_PSI_THRESHOLD: float = 0.2
    DRIFT_CHECK_INTERVAL_SECONDS: int = 300
    
    # Performance
    BATCH_SIZE: int = 32
    MAX_BATCH_SIZE: int = 1000
    INFERENCE_TIMEOUT_SECONDS: float = 30.0

    # Docker (optional)
    DOCKER_USERNAME: Optional[str] = None
    DOCKER_PASSWORD: Optional[str] = None

    # API Keys (optional)
    API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create directories if they don't exist
        for dir_path in [self.DATA_DIR, self.MODELS_DIR, self.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Set model paths if not specified
        if self.MODEL_PATH is None:
            self.MODEL_PATH = self.MODELS_DIR / f"{self.MODEL_NAME}_model.pkl"
        if self.SCALER_PATH is None:
            self.SCALER_PATH = self.MODELS_DIR / "standard_scaler.pkl"
        if self.LABEL_ENCODER_PATH is None:
            self.LABEL_ENCODER_PATH = self.MODELS_DIR / "label_encoder.pkl"
        if self.SELECTED_FEATURES_PATH is None:
            self.SELECTED_FEATURES_PATH = self.MODELS_DIR / "selected_features.pkl"


# Global settings instance
settings = Settings()


# Feature names from CICIDS2017 (63 selected features after feature engineering)
SELECTED_FEATURES = [
    'Destination_Port', 'Flow_Duration', 'Total_Fwd_Packets',
    'Total_Backward_Packets', 'Total_Length_of_Fwd_Packets',
    'Total_Length_of_Bwd_Packets', 'Fwd_Packet_Length_Max',
    'Fwd_Packet_Length_Min', 'Fwd_Packet_Length_Mean',
    'Fwd_Packet_Length_Std', 'Bwd_Packet_Length_Max',
    'Bwd_Packet_Length_Min', 'Bwd_Packet_Length_Mean',
    'Bwd_Packet_Length_Std', 'Flow_Bytes/s', 'Flow_Packets/s',
    'Flow_IAT_Mean', 'Flow_IAT_Std', 'Flow_IAT_Max', 'Flow_IAT_Min',
    'Fwd_IAT_Total', 'Fwd_IAT_Mean', 'Fwd_IAT_Std', 'Fwd_IAT_Max',
    'Fwd_IAT_Min', 'Bwd_IAT_Total', 'Bwd_IAT_Mean', 'Bwd_IAT_Std',
    'Bwd_IAT_Max', 'Bwd_IAT_Min', 'Fwd_PSH_Flags', 'Bwd_PSH_Flags',
    'Fwd_URG_Flags', 'Bwd_URG_Flags', 'Fwd_Header_Length',
    'Bwd_Header_Length', 'Fwd_Packets/s', 'Bwd_Packets/s',
    'Min_Packet_Length', 'Max_Packet_Length', 'Packet_Length_Mean',
    'Packet_Length_Std', 'Packet_Length_Variance', 'FIN_Flag_Count',
    'SYN_Flag_Count', 'RST_Flag_Count', 'PSH_Flag_Count',
    'ACK_Flag_Count', 'URG_Flag_Count', 'CWE_Flag_Count',
    'ECE_Flag_Count', 'Down/Up_Ratio', 'Average_Packet_Size',
    'Avg_Fwd_Segment_Size', 'Avg_Bwd_Segment_Size',
    'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
    'act_data_pkt_fwd', 'min_seg_size_forward', 'Active_Mean',
    'Active_Std', 'Active_Max', 'Active_Min', 'Idle_Mean'
]


# Label mapping from CICIDS2017
LABEL_MAPPING = {
    'BENIGN': 0,
    'DoS Hulk': 1,
    'PortScan': 2,
    'DDoS': 3,
    'DoS GoldenEye': 4,
    'FTP-Patator': 5,
    'SSH-Patator': 6,
    'DoS slowloris': 7,
    'DoS Slowhttptest': 8,
    'Bot': 9,
    'Web Attack_Brute Force': 10,
    'Web Attack_XSS': 11,
    'Infiltration': 12,
    'Web Attack_Sql Injection': 13,
    'Heartbleed': 14
}
