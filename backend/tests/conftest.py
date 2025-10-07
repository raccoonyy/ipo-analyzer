"""Pytest configuration and shared fixtures"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_ipo_metadata():
    """Sample IPO metadata for testing"""
    return pd.DataFrame(
        [
            {
                "company_name": "TestCompanyA",
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
            },
            {
                "company_name": "TestCompanyB",
                "code": "200000",
                "listing_date": "2024-02-20",
                "ipo_price_lower": 25000,
                "ipo_price_upper": 30000,
                "ipo_price_confirmed": 28000,
                "shares_offered": 500000,
                "institutional_demand_rate": 1200.0,
                "lockup_ratio": 30.0,
                "subscription_competition_rate": 1500.0,
                "paid_in_capital": 50000000000,
                "estimated_market_cap": 280000000000,
                "listing_method": "BOOK_BUILDING",
                "allocation_ratio_equal": 50.0,
                "allocation_ratio_proportional": 50.0,
                "industry": "BIOTECH",
                "theme": "HEALTHCARE",
            },
        ]
    )


@pytest.fixture
def sample_full_dataset():
    """Sample dataset with actual prices for testing"""
    return pd.DataFrame(
        [
            {
                "company_name": "TestCompanyA",
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
                "day1_high": 23000,
                "day1_close": 21500,
            }
        ]
    )


@pytest.fixture
def sample_intraday_data():
    """Sample intraday price data"""
    times = [f"{9+i//12:02d}:{(i%12)*5:02d}" for i in range(72)]
    return pd.DataFrame(
        {
            "time": times,
            "price": [20000 + i * 50 for i in range(72)],
            "volume": [1000] * 72,
        }
    )
