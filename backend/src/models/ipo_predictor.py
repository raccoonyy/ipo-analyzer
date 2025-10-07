"""
IPO Price Prediction Models
Train and evaluate models to predict IPO day and next day prices
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pickle
from pathlib import Path
from typing import Dict, Tuple, Any
import json
import logging

logger = logging.getLogger(__name__)


class IPOPricePredictor:
    """Train models to predict IPO execution prices"""

    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize predictor

        Args:
            model_type: Type of model ('random_forest' or 'gradient_boosting')
        """
        self.model_type = model_type
        self.models = {}
        self.metrics = {}

        # Initialize models for each target
        if model_type == "random_forest":
            base_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
        elif model_type == "gradient_boosting":
            base_model = GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Create separate models for each target
        self.models["day0_high"] = base_model
        self.models["day0_close"] = base_model.__class__(**base_model.get_params())
        self.models["day1_close"] = base_model.__class__(**base_model.get_params())

    def train(
        self, X: np.ndarray, y_dict: Dict[str, np.ndarray], test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train models for all target variables

        Args:
            X: Feature matrix (n_samples, n_features)
            y_dict: Dictionary of target arrays {'day0_high': [...], 'day0_close': [...], 'day1_close': [...]}
            test_size: Proportion of data to use for testing

        Returns:
            Dictionary of evaluation metrics
        """
        results = {}

        # Split data
        indices = np.arange(len(X))
        train_idx, test_idx = train_test_split(
            indices, test_size=test_size, random_state=42
        )

        X_train, X_test = X[train_idx], X[test_idx]

        # Train each model
        for target_name, y in y_dict.items():
            logger.info(f"Training model for {target_name}...")

            y_train, y_test = y[train_idx], y[test_idx]

            # Train
            self.models[target_name].fit(X_train, y_train)

            # Predict
            y_pred_train = self.models[target_name].predict(X_train)
            y_pred_test = self.models[target_name].predict(X_test)

            # Evaluate
            train_metrics = self._calculate_metrics(y_train, y_pred_train)
            test_metrics = self._calculate_metrics(y_test, y_pred_test)

            results[target_name] = {"train": train_metrics, "test": test_metrics}

            logger.info(
                f"  Train - MAE: {train_metrics['mae']:.2f}, RMSE: {train_metrics['rmse']:.2f}, R²: {train_metrics['r2']:.4f}"
            )
            logger.info(
                f"  Test  - MAE: {test_metrics['mae']:.2f}, RMSE: {test_metrics['rmse']:.2f}, R²: {test_metrics['r2']:.4f}"
            )

            # Feature importance (if available)
            if hasattr(self.models[target_name], "feature_importances_"):
                results[target_name]["feature_importance"] = self.models[
                    target_name
                ].feature_importances_.tolist()

        self.metrics = results
        return results

    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Generate predictions for all targets

        Args:
            X: Feature matrix

        Returns:
            Dictionary of predictions
        """
        predictions = {}

        for target_name, model in self.models.items():
            predictions[target_name] = model.predict(X)

        return predictions

    def _calculate_metrics(
        self, y_true: np.ndarray, y_pred: np.ndarray
    ) -> Dict[str, float]:
        """Calculate regression metrics"""
        return {
            "mae": mean_absolute_error(y_true, y_pred),
            "rmse": np.sqrt(mean_squared_error(y_true, y_pred)),
            "r2": r2_score(y_true, y_pred),
            "mape": np.mean(np.abs((y_true - y_pred) / y_true))
            * 100,  # Mean Absolute Percentage Error
        }

    def save_models(self, output_dir: str = "models"):
        """Save trained models"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save each model
        for target_name, model in self.models.items():
            model_file = output_path / f"model_{target_name}.pkl"
            with open(model_file, "wb") as f:
                pickle.dump(model, f)
            logger.info(f"Saved model for {target_name} to {model_file}")

        # Save metrics
        metrics_file = output_path / "metrics.json"
        with open(metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)
        logger.info(f"Saved metrics to {metrics_file}")

    def load_models(self, input_dir: str = "models"):
        """Load trained models"""
        input_path = Path(input_dir)

        for target_name in ["day0_high", "day0_close", "day1_close"]:
            model_file = input_path / f"model_{target_name}.pkl"
            if model_file.exists():
                with open(model_file, "rb") as f:
                    self.models[target_name] = pickle.load(f)
                logger.info(f"Loaded model for {target_name}")
            else:
                logger.warning(f"Model file not found for {target_name}")

        # Load metrics
        metrics_file = input_path / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                self.metrics = json.load(f)

    def get_feature_importance(
        self, feature_names: list, target_name: str = "day0_high", top_n: int = 10
    ) -> pd.DataFrame:
        """
        Get feature importance for a specific target

        Args:
            feature_names: List of feature names
            target_name: Target variable name
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importance
        """
        if target_name not in self.models:
            raise ValueError(f"Unknown target: {target_name}")

        model = self.models[target_name]

        if not hasattr(model, "feature_importances_"):
            return None

        importance_df = pd.DataFrame(
            {"feature": feature_names, "importance": model.feature_importances_}
        )

        importance_df = importance_df.sort_values("importance", ascending=False).head(
            top_n
        )

        return importance_df


if __name__ == "__main__":
    # Example usage
    from src.data_collection.ipo_collector import IPODataCollector
    from src.features.feature_engineering import IPOFeatureEngineer

    # Collect data
    collector = IPODataCollector()
    df = collector.collect_full_dataset(2022, 2025)

    # Engineer features
    engineer = IPOFeatureEngineer()
    X, y_dict, metadata = engineer.prepare_training_data(df)

    # Train model
    predictor = IPOPricePredictor(model_type="random_forest")
    results = predictor.train(X, y_dict)

    # Save models
    predictor.save_models()
    engineer.save_transformers()

    # Show feature importance
    for target in ["day0_high", "day0_close", "day1_close"]:
        print(f"\nTop features for {target}:")
        importance = predictor.get_feature_importance(engineer.feature_names, target)
        print(importance)
