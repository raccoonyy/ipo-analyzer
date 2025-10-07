"""Unit tests for PredictionGenerator"""

import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path
from src.prediction.generate_predictions import PredictionGenerator
from src.data_collection.ipo_collector import IPODataCollector
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor


class TestPredictionGenerator:
    """Test PredictionGenerator class"""

    @pytest.fixture
    def setup_models(self, temp_data_dir):
        """Setup trained models for testing"""
        np.random.seed(42)

        df = pd.DataFrame(
            [
                {
                    "company_name": "TestCompany",
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
                    "day0_high": 24000,
                    "day0_close": 22000,
                    "day1_close": 21500,
                }
            ]
        )

        engineer = IPOFeatureEngineer()
        X, y_dict, metadata = engineer.prepare_training_data(df)

        X_extended = np.tile(X, (50, 1))
        y_dict_extended = {key: np.tile(value, 50) for key, value in y_dict.items()}

        predictor = IPOPricePredictor(model_type="random_forest")
        predictor.train(X_extended, y_dict_extended, test_size=0.2)

        models_dir = Path(temp_data_dir) / "models"
        transformers_dir = Path(temp_data_dir) / "processed"
        models_dir.mkdir(parents=True, exist_ok=True)
        transformers_dir.mkdir(parents=True, exist_ok=True)

        predictor.save_models(str(models_dir))
        engineer.save_transformers(str(transformers_dir))

        return str(models_dir), str(transformers_dir)

    def test_init(self, setup_models):
        """Test generator initialization"""
        models_dir, transformers_dir = setup_models
        generator = PredictionGenerator(models_dir, transformers_dir)

        assert generator.predictor is not None
        assert generator.engineer is not None

    def test_generate_predictions_for_dataset(self, setup_models, sample_ipo_metadata):
        """Test prediction generation for dataset"""
        models_dir, transformers_dir = setup_models
        generator = PredictionGenerator(models_dir, transformers_dir)

        predictions = generator.generate_predictions_for_dataset(sample_ipo_metadata)

        assert isinstance(predictions, list)
        assert len(predictions) == len(sample_ipo_metadata)

        for pred in predictions:
            assert "company_name" in pred
            assert "code" in pred
            assert "listing_date" in pred
            assert "ipo_price" in pred
            assert "predicted" in pred
            assert "metadata" in pred

            assert "day0_high" in pred["predicted"]
            assert "day0_close" in pred["predicted"]
            assert "day1_close" in pred["predicted"]

            assert isinstance(pred["predicted"]["day0_high"], int)
            assert isinstance(pred["predicted"]["day0_close"], int)
            assert isinstance(pred["predicted"]["day1_close"], int)

    def test_generate_and_save(self, setup_models, temp_data_dir):
        """Test prediction generation and saving to JSON"""
        models_dir, transformers_dir = setup_models
        generator = PredictionGenerator(models_dir, transformers_dir)

        output_file = Path(temp_data_dir) / "test_predictions.json"

        collector = IPODataCollector(data_dir=temp_data_dir)
        collector.collect_ipo_metadata(2022, 2023)

        predictions = generator.generate_and_save(
            start_year=2022, end_year=2023, output_file=str(output_file)
        )

        assert output_file.exists()
        assert isinstance(predictions, list)
        assert len(predictions) > 0

        with open(output_file, "r", encoding="utf-8") as f:
            loaded_predictions = json.load(f)

        assert len(loaded_predictions) == len(predictions)
        assert loaded_predictions[0]["company_name"] == predictions[0]["company_name"]

    def test_prediction_format(self, setup_models, sample_ipo_metadata):
        """Test prediction output format"""
        models_dir, transformers_dir = setup_models
        generator = PredictionGenerator(models_dir, transformers_dir)

        predictions = generator.generate_predictions_for_dataset(sample_ipo_metadata)
        pred = predictions[0]

        assert isinstance(pred["company_name"], str)
        assert isinstance(pred["code"], str)
        assert isinstance(pred["listing_date"], str)
        assert isinstance(pred["ipo_price"], int)

        assert isinstance(pred["metadata"]["shares_offered"], int)
        assert isinstance(pred["metadata"]["institutional_demand_rate"], float)
        assert isinstance(pred["metadata"]["subscription_competition_rate"], float)
        assert isinstance(pred["metadata"]["industry"], str)
        assert isinstance(pred["metadata"]["theme"], str)

    def test_print_summary(self, setup_models, sample_ipo_metadata, capsys):
        """Test summary printing"""
        models_dir, transformers_dir = setup_models
        generator = PredictionGenerator(models_dir, transformers_dir)

        predictions = generator.generate_predictions_for_dataset(sample_ipo_metadata)
        generator._print_summary(predictions)

        captured = capsys.readouterr()
        assert "PREDICTION SUMMARY" in captured.out
        assert "Total IPOs:" in captured.out
        assert "Day 0 High Price:" in captured.out
