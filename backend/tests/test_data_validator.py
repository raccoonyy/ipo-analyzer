"""Unit tests for DataValidator"""

import pytest
import pandas as pd
import numpy as np
from src.validation.data_validator import DataValidator


class TestDataValidator:
    """Test DataValidator class"""

    def test_validate_ipo_metadata_valid(self, sample_ipo_metadata):
        """Test validation with valid data"""
        is_valid, errors = DataValidator.validate_ipo_metadata(sample_ipo_metadata)
        assert is_valid
        assert len(errors) == 0

    def test_validate_ipo_metadata_empty(self):
        """Test validation with empty DataFrame"""
        df = pd.DataFrame()
        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        assert not is_valid
        assert "empty" in errors[0].lower()

    def test_validate_ipo_metadata_missing_columns(self):
        """Test validation with missing columns"""
        df = pd.DataFrame({"company_name": ["Test"], "code": ["123"]})
        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        assert not is_valid
        assert any("Missing required columns" in error for error in errors)

    def test_validate_ipo_metadata_invalid_price_bounds(self):
        """Test validation with invalid price bounds"""
        df = pd.DataFrame(
            [
                {
                    "company_name": "Test",
                    "code": "123",
                    "listing_date": "2024-01-01",
                    "ipo_price_lower": 25000,
                    "ipo_price_upper": 20000,
                    "ipo_price_confirmed": 22000,
                    "shares_offered": 1000,
                    "institutional_demand_rate": 500,
                    "lockup_ratio": 30,
                    "subscription_competition_rate": 800,
                    "paid_in_capital": 10000,
                    "estimated_market_cap": 50000,
                    "listing_method": "GENERAL",
                    "allocation_ratio_equal": 50,
                    "allocation_ratio_proportional": 50,
                    "industry": "IT",
                    "theme": "TECH",
                }
            ]
        )
        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        assert not is_valid
        assert any("ipo_price_lower must be less than" in error for error in errors)

    def test_validate_ipo_metadata_negative_values(self):
        """Test validation with negative values"""
        df = pd.DataFrame(
            [
                {
                    "company_name": "Test",
                    "code": "123",
                    "listing_date": "2024-01-01",
                    "ipo_price_lower": 18000,
                    "ipo_price_upper": 22000,
                    "ipo_price_confirmed": 20000,
                    "shares_offered": -1000,
                    "institutional_demand_rate": -500,
                    "lockup_ratio": 30,
                    "subscription_competition_rate": -800,
                    "paid_in_capital": -10000,
                    "estimated_market_cap": -50000,
                    "listing_method": "GENERAL",
                    "allocation_ratio_equal": 50,
                    "allocation_ratio_proportional": 50,
                    "industry": "IT",
                    "theme": "TECH",
                }
            ]
        )
        is_valid, errors = DataValidator.validate_ipo_metadata(df)
        assert not is_valid
        assert len(errors) > 0

    def test_check_missing_values(self):
        """Test missing values detection"""
        df = pd.DataFrame(
            {
                "col1": [1, 2, None, 4],
                "col2": [1, None, None, 4],
                "col3": [1, 2, 3, 4],
            }
        )
        missing = DataValidator.check_missing_values(df)
        assert "col1" in missing
        assert "col2" in missing
        assert "col3" not in missing
        assert missing["col1"] == 1
        assert missing["col2"] == 2

    def test_check_outliers(self):
        """Test outlier detection"""
        df = pd.DataFrame({"values": [10, 12, 11, 13, 12, 100, 14, 11, 13, 12]})
        outliers = DataValidator.check_outliers(df, ["values"], n_std=2.0)
        assert "values" in outliers
        assert len(outliers["values"]) > 0

    def test_check_duplicates(self, sample_ipo_metadata):
        """Test duplicate detection"""
        df = pd.concat(
            [sample_ipo_metadata, sample_ipo_metadata.iloc[:1]], ignore_index=True
        )
        duplicates = DataValidator.check_duplicates(df, subset=["code"])
        assert len(duplicates) > 0

    def test_validate_date_range_valid(self):
        """Test date range validation with valid dates"""
        df = pd.DataFrame({"listing_date": ["2023-01-01", "2023-06-15", "2024-12-31"]})
        is_valid, errors = DataValidator.validate_date_range(
            df, "listing_date", 2023, 2024
        )
        assert is_valid
        assert len(errors) == 0

    def test_validate_date_range_invalid(self):
        """Test date range validation with invalid dates"""
        df = pd.DataFrame({"listing_date": ["2020-01-01", "2023-06-15", "2026-12-31"]})
        is_valid, errors = DataValidator.validate_date_range(
            df, "listing_date", 2023, 2024
        )
        assert not is_valid
        assert len(errors) == 2

    def test_generate_data_quality_report(self, sample_ipo_metadata):
        """Test data quality report generation"""
        report = DataValidator.generate_data_quality_report(sample_ipo_metadata)
        assert "total_rows" in report
        assert "total_columns" in report
        assert "missing_values" in report
        assert "duplicate_count" in report
        assert "data_types" in report
        assert report["total_rows"] == len(sample_ipo_metadata)
        assert report["total_columns"] == len(sample_ipo_metadata.columns)
