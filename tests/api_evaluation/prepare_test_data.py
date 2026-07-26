"""Prepare validation and test datasets for API evaluation.

This script:
1. Loads the full CICIDS2017 dataset
2. Applies preprocessing to match training pipeline
3. Splits into validation and test sets
4. Saves samples for API testing
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import joblib

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config import settings, SELECTED_FEATURES, LABEL_MAPPING
from shared.feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED = settings.RANDOM_SEED
np.random.seed(SEED)


def prepare_test_datasets(data_path: str, output_dir: str, n_validation: int = 1000, n_test: int = 1000):
    """Prepare validation and test datasets from the full dataset.
    
    Args:
        data_path: Path to CICIDS2017 CSV file
        output_dir: Output directory for test datasets
        n_validation: Number of validation samples
        n_test: Number of test samples
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    logger.info(f"Original dataset shape: {df.shape}")
    logger.info(f"Label distribution:\n{df['Label'].value_counts()}")
    
    # Apply preprocessing
    feature_engineer = FeatureEngineer()
    
    # Standardize column names
    df = feature_engineer.standardize_column_names(df)
    
    # Handle missing values
    df = feature_engineer.handle_missing_values(df, fit=False)
    
    # Remove constant features
    df = feature_engineer.remove_constant_features(df, fit=False)
    
    logger.info(f"After preprocessing: {df.shape}")
    
    # Stratified sampling for validation set
    validation_samples = []
    for label in df['Label'].unique():
        label_df = df[df['Label'] == label]
        n_samples = min(len(label_df), max(10, int(n_validation * len(label_df) / len(df))))
        validation_samples.append(label_df.sample(n=n_samples, random_state=SEED))
    
    validation_df = pd.concat(validation_samples, ignore_index=True).sample(frac=1, random_state=SEED)
    
    # Remove validation samples from remaining data
    remaining_df = df.drop(validation_df.index)
    
    # Stratified sampling for test set
    test_samples = []
    for label in remaining_df['Label'].unique():
        label_df = remaining_df[remaining_df['Label'] == label]
        n_samples = min(len(label_df), max(10, int(n_test * len(label_df) / len(remaining_df))))
        test_samples.append(label_df.sample(n=n_samples, random_state=SEED))
    
    test_df = pd.concat(test_samples, ignore_index=True).sample(frac=1, random_state=SEED)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save datasets
    validation_path = os.path.join(output_dir, 'validation_set.csv')
    test_path = os.path.join(output_dir, 'test_set.csv')
    
    validation_df.to_csv(validation_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved validation set: {validation_path} (shape: {validation_df.shape})")
    logger.info(f"Validation label distribution:\n{validation_df['Label'].value_counts()}")
    
    logger.info(f"Saved test set: {test_path} (shape: {test_df.shape})")
    logger.info(f"Test label distribution:\n{test_df['Label'].value_counts()}")
    
    # Save small samples for quick testing
    small_validation = validation_df.sample(n=min(100, len(validation_df)), random_state=SEED)
    small_test = test_df.sample(n=min(100, len(test_df)), random_state=SEED)
    
    small_validation.to_csv(os.path.join(output_dir, 'validation_small.csv'), index=False)
    small_test.to_csv(os.path.join(output_dir, 'test_small.csv'), index=False)
    
    logger.info(f"Saved small samples (100 each) for quick testing")
    
    return validation_df, test_df


def main():
    parser = argparse.ArgumentParser(description="Prepare test datasets for API evaluation")
    parser.add_argument("--data-path", type=str, default="./data/cicids2017.csv",
                       help="Path to CICIDS2017 CSV")
    parser.add_argument("--output-dir", type=str, default="./tests/api_evaluation/data",
                       help="Output directory for test datasets")
    parser.add_argument("--n-validation", type=int, default=1000,
                       help="Number of validation samples")
    parser.add_argument("--n-test", type=int, default=1000,
                       help="Number of test samples")
    
    args = parser.parse_args()
    
    prepare_test_datasets(
        data_path=args.data_path,
        output_dir=args.output_dir,
        n_validation=args.n_validation,
        n_test=args.n_test
    )
    
    logger.info("Test data preparation complete!")


if __name__ == "__main__":
    main()
