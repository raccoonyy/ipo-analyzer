"""Unit tests for IPOPricePredictor"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from src.models.ipo_predictor import IPOPricePredictor


class TestIPOPricePredictor:
    """Test IPOPricePredictor class"""

    def test_init_random_forest(self):
        """Test predictor initialization with Random Forest"""
        predictor = IPOPricePredictor(model_type="random_forest")
        assert predictor.model_type == "random_forest"
        assert "day0_high" in predictor.models
        assert "day0_close" in predictor.models
        assert "day1_close" in predictor.models

    def test_init_gradient_boosting(self):
        """Test predictor initialization with Gradient Boosting"""
        predictor = IPOPricePredictor(model_type="gradient_boosting")
        assert predictor.model_type == "gradient_boosting"

    def test_init_invalid_model(self):
        """Test predictor initialization with invalid model type"""
        with pytest.raises(ValueError):
            IPOPricePredictor(model_type="invalid_model")

    def test_train(self):
        """Test model training"""
        np.random.seed(42)
        X = np.random.randn(50, 19)
        y_dict = {
            "day0_high": np.random.randint(20000, 30000, 50),
            "day0_close": np.random.randint(18000, 28000, 50),
            "day1_close": np.random.randint(17000, 27000, 50),
        }

        predictor = IPOPricePredictor(model_type="random_forest")
        results = predictor.train(X, y_dict, test_size=0.2)

        assert isinstance(results, dict)
        assert "day0_high" in results
        assert "day0_close" in results
        assert "day1_close" in results

        for target_name, metrics in results.items():
            assert "train" in metrics
            assert "test" in metrics
            assert "mae" in metrics["train"]
            assert "rmse" in metrics["train"]
            assert "r2" in metrics["train"]
            assert "mape" in metrics["train"]

    def test_predict(self):
        """Test prediction generation"""
        np.random.seed(42)
        X_train = np.random.randn(50, 19)
        X_test = np.random.randn(10, 19)
        y_dict = {
            "day0_high": np.random.randint(20000, 30000, 50),
            "day0_close": np.random.randint(18000, 28000, 50),
            "day1_close": np.random.randint(17000, 27000, 50),
        }

        predictor = IPOPricePredictor(model_type="random_forest")
        predictor.train(X_train, y_dict, test_size=0.2)

        predictions = predictor.predict(X_test)

        assert isinstance(predictions, dict)
        assert "day0_high" in predictions
        assert "day0_close" in predictions
        assert "day1_close" in predictions
        assert len(predictions["day0_high"]) == 10
        assert len(predictions["day0_close"]) == 10
        assert len(predictions["day1_close"]) == 10

    def test_save_and_load_models(self, temp_data_dir):
        """Test saving and loading models"""
        np.random.seed(42)
        X = np.random.randn(50, 19)
        y_dict = {
            "day0_high": np.random.randint(20000, 30000, 50),
            "day0_close": np.random.randint(18000, 28000, 50),
            "day1_close": np.random.randint(17000, 27000, 50),
        }

        predictor = IPOPricePredictor(model_type="random_forest")
        predictor.train(X, y_dict, test_size=0.2)
        predictor.save_models(temp_data_dir)

        model_files = [
            "model_day0_high.pkl",
            "model_day0_close.pkl",
            "model_day1_close.pkl",
            "metrics.json",
        ]

        for filename in model_files:
            assert (Path(temp_data_dir) / filename).exists()

        new_predictor = IPOPricePredictor(model_type="random_forest")
        new_predictor.load_models(temp_data_dir)

        X_test = np.random.randn(5, 19)
        predictions1 = predictor.predict(X_test)
        predictions2 = new_predictor.predict(X_test)

        np.testing.assert_array_almost_equal(
            predictions1["day0_high"], predictions2["day0_high"]
        )

    def test_get_feature_importance(self):
        """Test feature importance extraction"""
        np.random.seed(42)
        X = np.random.randn(50, 19)
        y_dict = {
            "day0_high": np.random.randint(20000, 30000, 50),
            "day0_close": np.random.randint(18000, 28000, 50),
            "day1_close": np.random.randint(17000, 27000, 50),
        }

        feature_names = [f"feature_{i}" for i in range(19)]

        predictor = IPOPricePredictor(model_type="random_forest")
        predictor.train(X, y_dict, test_size=0.2)

        importance_df = predictor.get_feature_importance(
            feature_names, target_name="day0_high", top_n=10
        )

        assert isinstance(importance_df, pd.DataFrame)
        assert "feature" in importance_df.columns
        assert "importance" in importance_df.columns
        assert len(importance_df) <= 10

    def test_calculate_metrics(self):
        """Test metrics calculation"""
        predictor = IPOPricePredictor(model_type="random_forest")

        y_true = np.array([20000, 21000, 22000, 23000, 24000])
        y_pred = np.array([19500, 21500, 21800, 23200, 24100])

        metrics = predictor._calculate_metrics(y_true, y_pred)

        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert "mape" in metrics

        assert metrics["mae"] > 0
        assert metrics["rmse"] > 0
        assert 0 <= metrics["r2"] <= 1
        assert metrics["mape"] > 0
