"""Feature engineering utilities based on CICIDS2017 notebook preprocessing.

Extracted from AI_Powered_Cyber_Threat_Detection_and_intrusion_detection.ipynb
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Handle all feature engineering operations for CICIDS2017 data."""
    
    def __init__(self):
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.selected_features: Optional[List[str]] = None
        self.constant_features: Optional[List[str]] = None
        self.median_values: Optional[dict] = None
        
    def standardize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names by stripping spaces and replacing with underscores."""
        df.columns = (
            df.columns
            .str.strip()
            .str.replace(" ", "_", regex=False)
        )
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Impute missing values using median imputation.
        
        Args:
            df: Input dataframe
            fit: If True, compute median values. If False, use stored values.
        
        Returns:
            Dataframe with imputed values
        """
        if fit:
            # Compute median for numerical columns
            numerical_cols = df.select_dtypes(include=[np.number]).columns
            self.median_values = {
                col: df[col].median() 
                for col in numerical_cols if df[col].isnull().any()
            }
            logger.info(f"Computed median values for {len(self.median_values)} columns")
        
        # Fill missing values
        if self.median_values:
            df = df.fillna(self.median_values)
            logger.info(f"Imputed {sum(df.isnull().sum())} missing values")
        
        return df
    
    def remove_constant_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Remove features with zero variance.
        
        Args:
            df: Input dataframe
            fit: If True, identify constant features. If False, use stored list.
        
        Returns:
            Dataframe with constant features removed
        """
        if fit:
            self.constant_features = [
                col for col in df.columns
                if col != 'Label' and df[col].nunique(dropna=False) == 1
            ]
            logger.info(f"Identified {len(self.constant_features)} constant features")
        
        if self.constant_features:
            df = df.drop(columns=self.constant_features)
            logger.info(f"Removed {len(self.constant_features)} constant features")
        
        return df
    
    def encode_labels(self, labels: pd.Series, fit: bool = True) -> np.ndarray:
        """Encode categorical labels to integers.
        
        Args:
            labels: Series of categorical labels
            fit: If True, fit label encoder. If False, use stored encoder.
        
        Returns:
            Encoded labels
        """
        if fit:
            self.label_encoder = LabelEncoder()
            encoded = self.label_encoder.fit_transform(labels)
            logger.info(f"Encoded {len(self.label_encoder.classes_)} unique labels")
        else:
            if self.label_encoder is None:
                raise ValueError("Label encoder not fitted. Call with fit=True first.")
            encoded = self.label_encoder.transform(labels)
        
        return encoded
    
    def scale_features(self, X: pd.DataFrame, fit: bool = True) -> np.ndarray:
        """Standardize features using StandardScaler.
        
        Args:
            X: Feature dataframe
            fit: If True, fit scaler. If False, use stored scaler.
        
        Returns:
            Scaled feature array
        """
        if fit:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            logger.info(f"Fitted scaler on {X.shape[1]} features")
        else:
            if self.scaler is None:
                raise ValueError("Scaler not fitted. Call with fit=True first.")
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def select_features(self, df: pd.DataFrame, selected_features: Optional[List[str]] = None) -> pd.DataFrame:
        """Select specified features from dataframe.
        
        Args:
            df: Input dataframe
            selected_features: List of feature names to select
        
        Returns:
            Dataframe with selected features only
        """
        if selected_features is not None:
            self.selected_features = selected_features
        
        if self.selected_features is None:
            raise ValueError("No features selected. Provide selected_features list.")
        
        # Ensure all selected features exist
        missing = set(self.selected_features) - set(df.columns)
        if missing:
            raise ValueError(f"Missing features in dataframe: {missing}")
        
        return df[self.selected_features]
    
    def save_artifacts(self, base_path: str):
        """Save all preprocessing artifacts."""
        if self.scaler:
            joblib.dump(self.scaler, f"{base_path}/standard_scaler.pkl")
        if self.label_encoder:
            joblib.dump(self.label_encoder, f"{base_path}/label_encoder.pkl")
        if self.selected_features:
            joblib.dump(self.selected_features, f"{base_path}/selected_features.pkl")
        if self.median_values:
            joblib.dump(self.median_values, f"{base_path}/median_values.pkl")
        if self.constant_features:
            joblib.dump(self.constant_features, f"{base_path}/constant_features.pkl")
        logger.info(f"Saved all artifacts to {base_path}")
    
    def load_artifacts(self, base_path: str):
        """Load all preprocessing artifacts."""
        self.scaler = joblib.load(f"{base_path}/standard_scaler.pkl")
        self.label_encoder = joblib.load(f"{base_path}/label_encoder.pkl")
        self.selected_features = joblib.load(f"{base_path}/selected_features.pkl")
        logger.info(f"Loaded artifacts from {base_path}")
