"""Unit tests for IPOFeatureEngineer"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.features.feature_engineering import IPOFeatureEngineer


class TestIPOFeatureEngineer:
    """Test IPOFeatureEngineer class"""

    def test_init(self):
        """Test engineer initialization"""
        engineer = IPOFeatureEngineer()
        assert engineer.scaler is not None
        assert isinstance(engineer.label_encoders, dict)
        assert isinstance(engineer.feature_names, list)

    def test_engineer_features(self, sample_ipo_metadata):
        """Test feature engineering"""
        engineer = IPOFeatureEngineer()
        features_df = engineer.engineer_features(sample_ipo_metadata, fit=True)

        assert isinstance(features_df, pd.DataFrame)
        assert len(features_df) == len(sample_ipo_metadata)

        expected_features = [
            "listing_month",
            "listing_quarter",
            "listing_day_of_week",
            "ipo_price_range_pct",
            "price_positioning",
            "market_cap_ratio",
            "total_offering_value",
            "demand_to_lockup_ratio",
            "high_competition",
            "high_demand",
            "allocation_balance",
            "listing_method_encoded",
            "industry_encoded",
            "theme_encoded",
        ]

        for feature in expected_features:
            assert feature in features_df.columns

    def test_prepare_training_data(self, sample_full_dataset):
        """Test training data preparation"""
        engineer = IPOFeatureEngineer()
        X, y_dict, metadata = engineer.prepare_training_data(sample_full_dataset)

        assert isinstance(X, np.ndarray)
        assert X.shape[0] == len(sample_full_dataset)
        assert X.shape[1] == len(engineer.feature_names)

        assert "day0_high" in y_dict
        assert "day0_close" in y_dict
        assert "day1_close" in y_dict

        assert len(y_dict["day0_high"]) == len(sample_full_dataset)
        assert isinstance(metadata, pd.DataFrame)
        assert "company_name" in metadata.columns

    def test_save_and_load_transformers(self, temp_data_dir):
        """Test saving and loading transformers"""
        engineer = IPOFeatureEngineer()

        df = pd.DataFrame(
            [
                {
                    "company_name": "Test",
                    "code": "100000",
                    "listing_date": "2024-01-15",
                    "ipo_price_lower": 18000,
                    "ipo_price_upper": 22000,
                    "ipo_price_confirmed": 20000,
                    "shares_offered": 1000000,
                    "institutional_demand_rate": 500.0,
                    "lockup_ratio": 25.0,
                    "subscription_competition_rate": 800.0,
                    "paid_in_capital": 40000000000,
                    "estimated_market_cap": 200000000000,
                    "listing_method": "GENERAL",
                    "allocation_ratio_equal": 40.0,
                    "allocation_ratio_proportional": 60.0,
                    "industry": "IT",
                    "theme": "TECH",
                }
            ]
        )

        engineer.engineer_features(df, fit=True)
        engineer.save_transformers(temp_data_dir)

        scaler_file = Path(temp_data_dir) / "scaler.pkl"
        encoders_file = Path(temp_data_dir) / "label_encoders.pkl"
        features_file = Path(temp_data_dir) / "feature_names.pkl"

        assert scaler_file.exists()
        assert encoders_file.exists()
        assert features_file.exists()

        new_engineer = IPOFeatureEngineer()
        new_engineer.load_transformers(temp_data_dir)

        assert len(new_engineer.feature_names) > 0
        assert len(new_engineer.label_encoders) > 0

    def test_fit_transform_consistency(self, sample_ipo_metadata):
        """Test that fit=True and fit=False produce consistent results"""
        engineer = IPOFeatureEngineer()

        df_train = sample_ipo_metadata.iloc[:1].copy()
        df_test = sample_ipo_metadata.iloc[1:].copy()

        features_train = engineer.engineer_features(df_train, fit=True)
        features_test = engineer.engineer_features(df_test, fit=False)

        assert features_train.shape[1] == features_test.shape[1]

    def test_engineered_feature_values(self, sample_ipo_metadata):
        """Test engineered feature calculations"""
        engineer = IPOFeatureEngineer()
        features_df = engineer.engineer_features(sample_ipo_metadata, fit=True)

        assert len(features_df) == len(sample_ipo_metadata)
        assert "ipo_price_range_pct" in features_df.columns
        assert "market_cap_ratio" in features_df.columns
