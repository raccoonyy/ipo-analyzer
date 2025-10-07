"""
Data Validation Module
Validate IPO data quality and integrity
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validate IPO data quality and integrity"""

    @staticmethod
    def validate_ipo_metadata(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate IPO metadata DataFrame

        Args:
            df: DataFrame with IPO metadata

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if df is None or df.empty:
            errors.append("DataFrame is empty or None")
            return False, errors

        required_columns = [
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

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")

        for idx, row in df.iterrows():
            if pd.isna(row.get("company_name")) or row.get("company_name") == "":
                errors.append(f"Row {idx}: Missing company_name")

            if pd.isna(row.get("code")) or row.get("code") == "":
                errors.append(f"Row {idx}: Missing code")

            if "ipo_price_lower" in df.columns and "ipo_price_upper" in df.columns:
                if row["ipo_price_lower"] >= row["ipo_price_upper"]:
                    errors.append(
                        f"Row {idx}: ipo_price_lower must be less than ipo_price_upper"
                    )

            if (
                "ipo_price_confirmed" in df.columns
                and "ipo_price_lower" in df.columns
                and "ipo_price_upper" in df.columns
            ):
                if not (
                    row["ipo_price_lower"]
                    <= row["ipo_price_confirmed"]
                    <= row["ipo_price_upper"]
                ):
                    errors.append(
                        f"Row {idx}: ipo_price_confirmed must be between lower and upper bounds"
                    )

            if "shares_offered" in df.columns:
                if row["shares_offered"] <= 0:
                    errors.append(f"Row {idx}: shares_offered must be positive")

            if "institutional_demand_rate" in df.columns:
                if row["institutional_demand_rate"] < 0:
                    errors.append(
                        f"Row {idx}: institutional_demand_rate cannot be negative"
                    )

            if "lockup_ratio" in df.columns:
                if not (0 <= row["lockup_ratio"] <= 100):
                    errors.append(f"Row {idx}: lockup_ratio must be between 0 and 100")

            if "subscription_competition_rate" in df.columns:
                if row["subscription_competition_rate"] < 0:
                    errors.append(
                        f"Row {idx}: subscription_competition_rate cannot be negative"
                    )

            if "paid_in_capital" in df.columns:
                if row["paid_in_capital"] <= 0:
                    errors.append(f"Row {idx}: paid_in_capital must be positive")

            if "estimated_market_cap" in df.columns:
                if row["estimated_market_cap"] <= 0:
                    errors.append(f"Row {idx}: estimated_market_cap must be positive")

            if (
                "allocation_ratio_equal" in df.columns
                and "allocation_ratio_proportional" in df.columns
            ):
                total = (
                    row["allocation_ratio_equal"] + row["allocation_ratio_proportional"]
                )
                if not (99 <= total <= 101):
                    errors.append(
                        f"Row {idx}: allocation ratios must sum to ~100% (got {total}%)"
                    )

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def check_missing_values(df: pd.DataFrame) -> Dict[str, int]:
        """
        Check for missing values in DataFrame

        Args:
            df: DataFrame to check

        Returns:
            Dictionary of column names and missing value counts
        """
        missing = df.isnull().sum()
        return missing[missing > 0].to_dict()

    @staticmethod
    def check_outliers(
        df: pd.DataFrame, columns: List[str], n_std: float = 3.0
    ) -> Dict[str, List[int]]:
        """
        Detect outliers using standard deviation method

        Args:
            df: DataFrame to check
            columns: List of column names to check
            n_std: Number of standard deviations for outlier threshold

        Returns:
            Dictionary of column names and indices of outliers
        """
        outliers = {}

        for col in columns:
            if col not in df.columns:
                continue

            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            mean = df[col].mean()
            std = df[col].std()

            if std == 0:
                continue

            lower_bound = mean - n_std * std
            upper_bound = mean + n_std * std

            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_indices = df[outlier_mask].index.tolist()

            if outlier_indices:
                outliers[col] = outlier_indices

        return outliers

    @staticmethod
    def check_duplicates(df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
        """
        Check for duplicate rows

        Args:
            df: DataFrame to check
            subset: List of columns to check for duplicates (None = all columns)

        Returns:
            DataFrame of duplicate rows
        """
        duplicates = df[df.duplicated(subset=subset, keep=False)]
        return duplicates

    @staticmethod
    def validate_date_range(
        df: pd.DataFrame, date_column: str, start_year: int, end_year: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate dates are within expected range

        Args:
            df: DataFrame to check
            date_column: Name of date column
            start_year: Expected start year
            end_year: Expected end year

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        if date_column not in df.columns:
            errors.append(f"Date column '{date_column}' not found")
            return False, errors

        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])

        for idx, row in df_copy.iterrows():
            date = row[date_column]
            if date.year < start_year or date.year > end_year:
                errors.append(
                    f"Row {idx}: Date {date} is outside expected range {start_year}-{end_year}"
                )

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def generate_data_quality_report(df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive data quality report

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with data quality metrics
        """
        report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_values": DataValidator.check_missing_values(df),
            "duplicate_count": len(
                df[df.duplicated(subset=["code", "listing_date"], keep=False)]
            ),
            "data_types": df.dtypes.astype(str).to_dict(),
        }

        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_columns:
            report["numeric_summary"] = df[numeric_columns].describe().to_dict()

        return report
