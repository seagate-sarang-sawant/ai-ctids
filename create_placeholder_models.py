"""Create placeholder models for testing the inference API.

WARNING: These are NOT real trained models! 
Use only for testing infrastructure, not for actual predictions.
"""

import pickle
import numpy as np
from pathlib import Path

# Create models directory if it doesn't exist
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

print("Creating placeholder models for testing...")

# 1. Create a simple XGBoost-like model using sklearn's DummyClassifier
from sklearn.dummy import DummyClassifier

# Create a dummy classifier that predicts the most frequent class
xgboost_model = DummyClassifier(strategy="most_frequent")
# Fit with dummy data (15 classes for CICIDS2017)
X_dummy = np.random.rand(100, 63)  # 63 features
y_dummy = np.random.randint(0, 15, size=100)  # 15 classes
xgboost_model.fit(X_dummy, y_dummy)

with open(models_dir / "xgboost_model.pkl", "wb") as f:
    pickle.dump(xgboost_model, f)
print("✓ Created xgboost_model.pkl")

# 2. Create label encoder
from sklearn.preprocessing import LabelEncoder

label_encoder = LabelEncoder()
label_encoder.classes_ = np.array([
    'BENIGN', 'DoS Hulk', 'PortScan', 'DDoS', 'DoS GoldenEye',
    'FTP-Patator', 'SSH-Patator', 'DoS slowloris', 'DoS Slowhttptest',
    'Bot', 'Web Attack_Brute Force', 'Web Attack_XSS', 'Infiltration',
    'Web Attack_Sql Injection', 'Heartbleed'
])

with open(models_dir / "label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)
print("✓ Created label_encoder.pkl")

# 3. Create standard scaler
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
# Fit with dummy data
scaler.fit(X_dummy)

with open(models_dir / "standard_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
print("✓ Created standard_scaler.pkl")

# 4. Create selected features list
selected_features = [
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

with open(models_dir / "selected_features.pkl", "wb") as f:
    pickle.dump(selected_features, f)
print("✓ Created selected_features.pkl")

# 5. Create median values for imputation
median_values = {feature: 0.0 for feature in selected_features}
with open(models_dir / "median_values.pkl", "wb") as f:
    pickle.dump(median_values, f)
print("✓ Created median_values.pkl")

print("\n" + "="*60)
print("WARNING: These are PLACEHOLDER models for testing only!")
print("They will return random predictions, not real threat detection.")
print("="*60)
print("\nTo use real models, you need to:")
print("1. Get the CICIDS2017 dataset")
print("2. Run: make train")
print("3. Restart services: docker compose restart")
print("\nFiles created in models/ directory:")
print("- xgboost_model.pkl")
print("- label_encoder.pkl")
print("- standard_scaler.pkl")
print("- selected_features.pkl")
print("- median_values.pkl")
