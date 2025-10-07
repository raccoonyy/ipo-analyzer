"""Unit tests for Settings"""

import pytest
import os
from src.config.settings import Settings


class TestSettings:
    """Test Settings class"""

    def test_default_values(self):
        """Test default configuration values"""
        assert Settings.ENVIRONMENT == "development"
        assert Settings.LOG_LEVEL == "INFO"
        assert Settings.DATA_START_YEAR == 2022
        assert Settings.DATA_END_YEAR == 2025
        assert Settings.MODEL_TYPE == "random_forest"

    def test_is_development(self):
        """Test development environment check"""
        assert Settings.is_development() is True
        assert Settings.is_production() is False

    def test_model_settings(self):
        """Test model configuration"""
        assert Settings.RF_N_ESTIMATORS == 100
        assert Settings.RF_MAX_DEPTH == 15
        assert Settings.MODEL_TEST_SIZE == 0.2
        assert Settings.MODEL_RANDOM_STATE == 42

    def test_api_settings(self):
        """Test API configuration"""
        assert Settings.KRX_API_TIMEOUT == 30
        assert Settings.KRX_API_RETRY_ATTEMPTS == 3
        assert "api.krx.co.kr" in Settings.KRX_API_BASE_URL.lower()

    def test_data_directories(self):
        """Test data directory configuration"""
        assert Settings.DATA_RAW_DIR == "data/raw"
        assert Settings.DATA_PROCESSED_DIR == "data/processed"
        assert Settings.MODELS_DIR == "models"
        assert Settings.OUTPUT_DIR == "output"
