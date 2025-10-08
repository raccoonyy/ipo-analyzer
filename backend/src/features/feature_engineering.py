"""
Feature Engineering Pipeline
Transform raw IPO metadata into ML-ready features
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)


class IPOFeatureEngineer:
    """Transform raw IPO data into features for model training"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []

    def engineer_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Create engineered features from raw IPO metadata

        Args:
            df: DataFrame with raw IPO metadata
            fit: Whether to fit transformers (True for training, False for prediction)

        Returns:
            DataFrame with engineered features
        """
        df = df.copy()

        # Convert date to datetime
        df["listing_date"] = pd.to_datetime(df["listing_date"])

        # Create temporal features
        df["listing_month"] = df["listing_date"].dt.month
        df["listing_quarter"] = df["listing_date"].dt.quarter
        df["listing_day_of_week"] = df["listing_date"].dt.dayofweek

        # Price-related features
        df["ipo_price_range"] = df["ipo_price_upper"] - df["ipo_price_lower"]
        df["ipo_price_range_pct"] = (
            df["ipo_price_range"] / df["ipo_price_lower"]
        ) * 100
        df["price_positioning"] = (
            df["ipo_price_confirmed"] - df["ipo_price_lower"]
        ) / df["ipo_price_range"]

        # Market cap features
        df["market_cap_ratio"] = df["estimated_market_cap"] / df["paid_in_capital"]
        df["total_offering_value"] = df["shares_offered"] * df["ipo_price_confirmed"]

        # Demand indicators
        df["demand_to_lockup_ratio"] = df["institutional_demand_rate"] / (
            df["lockup_ratio"] + 1
        )
        df["high_competition"] = (df["subscription_competition_rate"] > 1000).astype(
            int
        )
        df["high_demand"] = (df["institutional_demand_rate"] > 500).astype(int)

        # Allocation features
        df["allocation_balance"] = abs(
            df["allocation_ratio_equal"] - df["allocation_ratio_proportional"]
        )

        # Categorical encoding
        categorical_cols = ["listing_method", "industry", "theme"]

        for col in categorical_cols:
            if fit:
                le = LabelEncoder()
                df[f"{col}_encoded"] = le.fit_transform(df[col])
                self.label_encoders[col] = le
            else:
                if col in self.label_encoders:
                    # Handle unseen categories
                    le = self.label_encoders[col]
                    df[f"{col}_encoded"] = df[col].apply(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
                else:
                    df[f"{col}_encoded"] = -1

        # Select feature columns for model
        # Use stored feature names if available (for prediction)
        if not fit and hasattr(self, 'feature_names') and self.feature_names:
            feature_cols = self.feature_names
        else:
            feature_cols = [
                "ipo_price_confirmed",
                "shares_offered",
                "institutional_demand_rate",
                "lockup_ratio",
                "subscription_competition_rate",
                "market_cap_ratio",
                "total_offering_value",
                "ipo_price_range_pct",
                "price_positioning",
                "demand_to_lockup_ratio",
                "allocation_balance",
                "high_competition",
                "high_demand",
                "listing_month",
                "listing_quarter",
                "listing_day_of_week",
                "listing_method_encoded",
                "industry_encoded",
                "theme_encoded",
                # KIS API daily indicators
                "day0_volume_kis",
                "day0_trading_value",
                "day1_volume",
                "day1_trading_value",
                "day0_turnover_rate",
                "day1_turnover_rate",
                "day0_volatility",
            ]

        # Store feature names
        if fit:
            self.feature_names = feature_cols

        # Create feature matrix
        # Fill missing columns with 0
        X = df[feature_cols].copy()

        # Scale numerical features
        if fit:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)

        # Create DataFrame with scaled features
        X_scaled_df = pd.DataFrame(X_scaled, columns=feature_cols, index=df.index)

        # Add metadata columns back
        metadata_cols = ["company_name", "code", "listing_date"]
        for col in metadata_cols:
            if col in df.columns:
                X_scaled_df[col] = df[col].values

        return X_scaled_df

    def prepare_training_data(self, df: pd.DataFrame) -> tuple:
        """
        Prepare data for model training

        Returns:
            X: Feature matrix
            y_dict: Dictionary of target variables
            metadata: Company identification data
        """
        # Engineer features
        features_df = self.engineer_features(df, fit=True)

        # Prepare feature matrix
        X = features_df[self.feature_names].values

        # Prepare targets
        y_dict = {
            "day0_high": df["day0_high"].values,
            "day0_close": df["day0_close"].values,
            "day1_close": df["day1_close"].values,
        }

        # Metadata for tracking
        metadata = df[["company_name", "code", "listing_date"]].copy()

        return X, y_dict, metadata

    def save_transformers(self, output_dir: str = "data/processed"):
        """Save fitted transformers for later use"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save scaler
        with open(output_path / "scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)

        # Save label encoders
        with open(output_path / "label_encoders.pkl", "wb") as f:
            pickle.dump(self.label_encoders, f)

        # Save feature names
        with open(output_path / "feature_names.pkl", "wb") as f:
            pickle.dump(self.feature_names, f)

        logger.info(f"Saved transformers to {output_path}")

    def load_transformers(self, input_dir: str = "data/processed"):
        """Load fitted transformers"""
        input_path = Path(input_dir)

        with open(input_path / "scaler.pkl", "rb") as f:
            self.scaler = pickle.load(f)

        with open(input_path / "label_encoders.pkl", "rb") as f:
            self.label_encoders = pickle.load(f)

        with open(input_path / "feature_names.pkl", "rb") as f:
            self.feature_names = pickle.load(f)

        logger.info(f"Loaded transformers from {input_path}")


if __name__ == "__main__":
    # Example usage
    from src.data_collection.ipo_collector import IPODataCollector

    collector = IPODataCollector()
    df = collector.collect_full_dataset(2022, 2025)

    engineer = IPOFeatureEngineer()
    X, y_dict, metadata = engineer.prepare_training_data(df)

    print(f"Feature matrix shape: {X.shape}")
    print(f"Target shapes: {[(k, v.shape) for k, v in y_dict.items()]}")

    engineer.save_transformers()
