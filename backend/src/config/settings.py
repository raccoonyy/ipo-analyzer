"""
Application Settings
Load configuration from environment variables and config files
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""

    # KRX API Configuration
    KRX_API_BASE_URL: str = os.getenv("KRX_API_BASE_URL", "https://api.krx.co.kr")
    KRX_API_KEY: Optional[str] = os.getenv("KRX_API_KEY")
    KRX_API_SECRET: Optional[str] = os.getenv("KRX_API_SECRET")
    KRX_API_TIMEOUT: int = int(os.getenv("KRX_API_TIMEOUT", "30"))
    KRX_API_RETRY_ATTEMPTS: int = int(os.getenv("KRX_API_RETRY_ATTEMPTS", "3"))

    # Application Settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/ipo_analyzer.log")

    # Data Settings
    DATA_START_YEAR: int = int(os.getenv("DATA_START_YEAR", "2022"))
    DATA_END_YEAR: int = int(os.getenv("DATA_END_YEAR", "2025"))
    DATA_RAW_DIR: str = os.getenv("DATA_RAW_DIR", "data/raw")
    DATA_PROCESSED_DIR: str = os.getenv("DATA_PROCESSED_DIR", "data/processed")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "models")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    # Model Settings
    MODEL_TYPE: str = os.getenv("MODEL_TYPE", "random_forest")
    RF_N_ESTIMATORS: int = int(os.getenv("RF_N_ESTIMATORS", "100"))
    RF_MAX_DEPTH: int = int(os.getenv("RF_MAX_DEPTH", "15"))
    RF_MIN_SAMPLES_SPLIT: int = int(os.getenv("RF_MIN_SAMPLES_SPLIT", "5"))
    RF_MIN_SAMPLES_LEAF: int = int(os.getenv("RF_MIN_SAMPLES_LEAF", "2"))
    MODEL_TEST_SIZE: float = float(os.getenv("MODEL_TEST_SIZE", "0.2"))
    MODEL_RANDOM_STATE: int = int(os.getenv("MODEL_RANDOM_STATE", "42"))

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT.lower() == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT.lower() == "development"

    @classmethod
    def validate(cls) -> None:
        """Validate required settings"""
        if cls.is_production():
            if not cls.KRX_API_KEY:
                raise ValueError("KRX_API_KEY is required in production")
            if not cls.KRX_API_SECRET:
                raise ValueError("KRX_API_SECRET is required in production")


# Create singleton instance
settings = Settings()
