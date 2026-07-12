"""Training pipeline with W&B tracking for Logistic Regression, XGBoost, and ANN.

Based on AI_Powered_Cyber_Threat_Detection_and_intrusion_detection.ipynb
"""

import os
import sys
import argparse
import logging
import time
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import joblib
import wandb

# Scikit-learn
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)

# XGBoost
from xgboost import XGBClassifier

# TensorFlow/Keras
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization, Input
from tensorflow.keras.callbacks import EarlyStopping

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from shared.config import settings, SELECTED_FEATURES, LABEL_MAPPING
from shared.feature_engineering import FeatureEngineer

# Setup
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set seeds for reproducibility
SEED = settings.RANDOM_SEED
np.random.seed(SEED)
tf.random.set_seed(SEED)


class ModelTrainer:
    """Orchestrates training of multiple models with W&B tracking."""
    
    def __init__(self, data_path: str, output_dir: str, use_wandb: bool = True):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_wandb = use_wandb
        
        self.feature_engineer = FeatureEngineer()
        self.X_train = None
        self.X_val = None
        self.X_test = None
        self.y_train = None
        self.y_val = None
        self.y_test = None
        
        if self.use_wandb:
            wandb.init(
                project=settings.WANDB_PROJECT,
                entity=settings.WANDB_ENTITY,
                config={
                    "random_seed": SEED,
                    "train_split": settings.TRAIN_SPLIT,
                    "val_split": settings.VAL_SPLIT,
                    "test_split": settings.TEST_SPLIT,
                }
            )
    
    def load_and_preprocess_data(self):
        """Load CICIDS2017 data and apply preprocessing."""
        logger.info(f"Loading data from {self.data_path}")
        df = pd.read_csv(self.data_path)
        logger.info(f"Loaded {len(df):,} rows with {len(df.columns)} columns")
        
        # Standardize column names
        df = self.feature_engineer.standardize_column_names(df)
        
        # Handle missing values
        df = self.feature_engineer.handle_missing_values(df, fit=True)
        
        # Remove constant features
        df = self.feature_engineer.remove_constant_features(df, fit=True)
        
        # Separate features and labels
        X = df.drop('Label', axis=1)
        y = df['Label']
        
        # Encode labels
        y_encoded = self.feature_engineer.encode_labels(y, fit=True)
        
        # Select features (use predefined or feature selection)
        if SELECTED_FEATURES:
            self.feature_engineer.selected_features = [
                f for f in SELECTED_FEATURES if f in X.columns
            ]
            X = self.feature_engineer.select_features(X)
        
        logger.info(f"Using {X.shape[1]} features after preprocessing")
        
        # Train/val/test split
        X_temp, self.X_test, y_temp, self.y_test = train_test_split(
            X, y_encoded,
            test_size=settings.TEST_SPLIT,
            random_state=SEED,
            stratify=y_encoded
        )
        
        val_ratio = settings.VAL_SPLIT / (settings.TRAIN_SPLIT + settings.VAL_SPLIT)
        self.X_train, self.X_val, self.y_train, self.y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_ratio,
            random_state=SEED,
            stratify=y_temp
        )
        
        logger.info(f"Train: {len(self.X_train):,}, Val: {len(self.X_val):,}, Test: {len(self.X_test):,}")
        
        # Scale features
        self.X_train = self.feature_engineer.scale_features(self.X_train, fit=True)
        self.X_val = self.feature_engineer.scale_features(self.X_val, fit=False)
        self.X_test = self.feature_engineer.scale_features(self.X_test, fit=False)
        
        # Save preprocessing artifacts
        self.feature_engineer.save_artifacts(str(self.output_dir))
        
        return self
    
    def log_metrics(self, model_name: str, y_true, y_pred, y_proba=None, training_time=None):
        """Log metrics to console and W&B."""
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision_macro": precision_score(y_true, y_pred, average='macro', zero_division=0),
            "recall_macro": recall_score(y_true, y_pred, average='macro', zero_division=0),
            "f1_macro": f1_score(y_true, y_pred, average='macro', zero_division=0),
        }
        
        if y_proba is not None:
            try:
                metrics["roc_auc"] = roc_auc_score(
                    y_true, y_proba,
                    multi_class='ovr',
                    average='macro'
                )
            except Exception as e:
                logger.warning(f"Could not compute ROC AUC: {e}")

        if training_time:
            metrics["training_time_seconds"] = training_time

        logger.info(f"\n{model_name} Metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric}: {value:.4f}")

        if self.use_wandb:
            wandb.log({f"{model_name}/{k}": v for k, v in metrics.items()})

        return metrics

    def train_logistic_regression(self):
        """Train Logistic Regression baseline model."""
        logger.info("\n" + "="*80)
        logger.info("Training Logistic Regression")
        logger.info("="*80)

        start_time = time.time()

        model = LogisticRegression(
            random_state=SEED,
            class_weight='balanced',
            max_iter=500,
            solver='lbfgs',
            multi_class='multinomial',
            n_jobs=-1
        )

        model.fit(self.X_train, self.y_train)
        training_time = time.time() - start_time

        # Predictions
        y_pred = model.predict(self.X_test)
        y_proba = model.predict_proba(self.X_test)

        # Log metrics
        metrics = self.log_metrics("logistic_regression", self.y_test, y_pred, y_proba, training_time)

        # Save model
        model_path = self.output_dir / "logistic_regression.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Saved model to {model_path}")

        if self.use_wandb:
            wandb.log_model(path=str(model_path), name="logistic_regression")

        return model, metrics

    def train_xgboost(self, tune_hyperparameters: bool = True):
        """Train XGBoost with optional hyperparameter tuning."""
        logger.info("\n" + "="*80)
        logger.info("Training XGBoost")
        logger.info("="*80)

        if tune_hyperparameters:
            param_grid = {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.1, 0.3],
                'max_depth': [6, 8, 10],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
            }

            base_model = XGBClassifier(
                objective='multi:softprob',
                num_class=len(np.unique(self.y_train)),
                eval_metric='mlogloss',
                tree_method='hist',
                random_state=SEED,
                n_jobs=-1
            )

            logger.info("Running hyperparameter search...")
            search = RandomizedSearchCV(
                base_model,
                param_grid,
                n_iter=10,
                scoring='f1_macro',
                cv=3,
                random_state=SEED,
                n_jobs=-1,
                verbose=1
            )

            start_time = time.time()
            search.fit(self.X_train, self.y_train)

            model = search.best_estimator_
            best_params = search.best_params_

            logger.info(f"Best parameters: {best_params}")
            if self.use_wandb:
                wandb.config.update({"xgboost_best_params": best_params})
        else:
            start_time = time.time()
            model = XGBClassifier(
                objective='multi:softprob',
                num_class=len(np.unique(self.y_train)),
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric='mlogloss',
                tree_method='hist',
                random_state=SEED,
                n_jobs=-1
            )
            model.fit(
                self.X_train, self.y_train,
                eval_set=[(self.X_val, self.y_val)],
                verbose=False
            )

        training_time = time.time() - start_time

        # Predictions
        y_pred = model.predict(self.X_test)
        y_proba = model.predict_proba(self.X_test)

        # Log metrics
        metrics = self.log_metrics("xgboost", self.y_test, y_pred, y_proba, training_time)

        # Save model
        model_path = self.output_dir / "xgboost_model.pkl"
        joblib.dump(model, model_path)
        logger.info(f"Saved model to {model_path}")

        if self.use_wandb:
            wandb.log_model(path=str(model_path), name="xgboost")

            # Log feature importance
            importance_df = pd.DataFrame({
                'feature': self.feature_engineer.selected_features,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)

            wandb.log({"xgboost/feature_importance": wandb.Table(dataframe=importance_df.head(20))})

        return model, metrics

    def train_ann(self):
        """Train Artificial Neural Network with Keras."""
        logger.info("\n" + "="*80)
        logger.info("Training ANN")
        logger.info("="*80)

        n_features = self.X_train.shape[1]
        n_classes = len(np.unique(self.y_train))

        # Build model
        model = Sequential([
            Input(shape=(n_features,)),
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(64, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(n_classes, activation='softmax')
        ])

        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        # Early stopping
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )

        # Train
        start_time = time.time()
        history = model.fit(
            self.X_train, self.y_train,
            validation_data=(self.X_val, self.y_val),
            epochs=30,
            batch_size=1024,
            callbacks=[early_stop],
            verbose=1
        )
        training_time = time.time() - start_time

        # Predictions
        y_proba = model.predict(self.X_test)
        y_pred = np.argmax(y_proba, axis=1)

        # Log metrics
        metrics = self.log_metrics("ann", self.y_test, y_pred, y_proba, training_time)

        # Save model
        model_path = self.output_dir / "ann_model.keras"
        model.save(model_path)
        logger.info(f"Saved model to {model_path}")

        if self.use_wandb:
            wandb.log_model(path=str(model_path), name="ann")

            # Log training history
            for epoch, (loss, acc, val_loss, val_acc) in enumerate(zip(
                history.history['loss'],
                history.history['accuracy'],
                history.history['val_loss'],
                history.history['val_accuracy']
            )):
                wandb.log({
                    "ann/epoch": epoch,
                    "ann/train_loss": loss,
                    "ann/train_accuracy": acc,
                    "ann/val_loss": val_loss,
                    "ann/val_accuracy": val_acc
                })

        return model, metrics

    def run(self, models_to_train: list = None):
        """Run complete training pipeline."""
        if models_to_train is None:
            models_to_train = ["logistic_regression", "xgboost", "ann"]

        logger.info("Starting training pipeline")
        self.load_and_preprocess_data()

        results = {}

        if "logistic_regression" in models_to_train:
            lr_model, lr_metrics = self.train_logistic_regression()
            results["logistic_regression"] = {"model": lr_model, "metrics": lr_metrics}

        if "xgboost" in models_to_train:
            xgb_model, xgb_metrics = self.train_xgboost(tune_hyperparameters=False)
            results["xgboost"] = {"model": xgb_model, "metrics": xgb_metrics}

        if "ann" in models_to_train:
            ann_model, ann_metrics = self.train_ann()
            results["ann"] = {"model": ann_model, "metrics": ann_metrics}

        # Compare models
        logger.info("\n" + "="*80)
        logger.info("Model Comparison")
        logger.info("="*80)

        comparison_df = pd.DataFrame({
            name: data["metrics"]
            for name, data in results.items()
        }).T

        logger.info(f"\n{comparison_df}")

        if self.use_wandb:
            wandb.log({"model_comparison": wandb.Table(dataframe=comparison_df)})
            wandb.finish()

        logger.info("\nTraining pipeline completed successfully!")
        return results


def main():
    """Main training entry point."""
    parser = argparse.ArgumentParser(description="Train AI-CTIDS models")
    parser.add_argument("--data-path", type=str, required=True, help="Path to CICIDS2017 CSV")
    parser.add_argument("--output-dir", type=str, default="./models", help="Output directory for models")
    parser.add_argument("--models", nargs="+", default=["logistic_regression", "xgboost", "ann"],
                       choices=["logistic_regression", "xgboost", "ann"], help="Models to train")
    parser.add_argument("--no-wandb", action="store_true", help="Disable W&B tracking")

    args = parser.parse_args()

    trainer = ModelTrainer(
        data_path=args.data_path,
        output_dir=args.output_dir,
        use_wandb=not args.no_wandb
    )

    results = trainer.run(models_to_train=args.models)

    return results


if __name__ == "__main__":
    main()
