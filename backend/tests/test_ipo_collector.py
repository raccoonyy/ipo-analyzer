"""Unit tests for IPODataCollector"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from src.data_collection.ipo_collector import IPODataCollector


class TestIPODataCollector:
    """Test IPODataCollector class"""

    def test_init(self, temp_data_dir):
        """Test collector initialization"""
        collector = IPODataCollector(data_dir=temp_data_dir)
        assert collector.data_dir.exists()
        assert collector.data_dir == Path(temp_data_dir)

    def test_collect_ipo_metadata(self, temp_data_dir):
        """Test IPO metadata collection"""
        collector = IPODataCollector(data_dir=temp_data_dir)
        df = collector.collect_ipo_metadata(2022, 2025)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        required_cols = [
            "company_name",
            "code",
            "listing_date",
            "ipo_price_lower",
            "ipo_price_upper",
            "ipo_price_confirmed",
            "shares_offered",
            "institutional_demand_rate",
            "lockup_ratio",
            "subscription_competition_rate",
            "paid_in_capital",
            "estimated_market_cap",
            "listing_method",
            "allocation_ratio_equal",
            "allocation_ratio_proportional",
            "industry",
            "theme",
        ]
        for col in required_cols:
            assert col in df.columns

        output_file = Path(temp_data_dir) / "ipo_metadata_2022_2025.csv"
        assert output_file.exists()

    def test_collect_intraday_prices(self, temp_data_dir):
        """Test intraday price collection"""
        collector = IPODataCollector(data_dir=temp_data_dir)
        date = datetime(2024, 1, 15)
        df = collector.collect_intraday_prices("100000", date)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "time" in df.columns
        assert "price" in df.columns
        assert "volume" in df.columns

        output_file = Path(temp_data_dir) / "intraday_100000_20240115.csv"
        assert output_file.exists()

    def test_get_highest_and_closing_price(self, temp_data_dir):
        """Test extraction of highest and closing prices"""
        collector = IPODataCollector(data_dir=temp_data_dir)
        date = datetime(2024, 1, 15)
        prices = collector.get_highest_and_closing_price("100000", date)

        assert "highest" in prices
        assert "closing" in prices
        assert isinstance(prices["highest"], (int, float, np.integer, np.floating))
        assert isinstance(prices["closing"], (int, float, np.integer, np.floating))
        assert prices["highest"] >= prices["closing"]

    def test_collect_full_dataset(self, temp_data_dir):
        """Test full dataset collection"""
        collector = IPODataCollector(data_dir=temp_data_dir)
        df = collector.collect_full_dataset(2022, 2025)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        assert "day0_high" in df.columns
        assert "day0_close" in df.columns
        assert "day1_high" in df.columns
        assert "day1_close" in df.columns

        for _, row in df.iterrows():
            assert row["day0_high"] >= row["day0_close"]

        output_file = Path(temp_data_dir) / "ipo_full_dataset_2022_2025.csv"
        assert output_file.exists()
