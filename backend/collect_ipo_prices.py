"""
Collect actual IPO offering prices from KIS API
Uses 예탁원정보(공모주청약일정) API to get real IPO prices
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from src.api.kis_client import KISApiClient
from src.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def collect_ipo_offering_data(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Collect IPO offering information from KIS API

    Args:
        start_year: Starting year (e.g., 2022)
        end_year: Ending year (e.g., 2025)

    Returns:
        DataFrame with IPO offering information
    """
    client = KISApiClient()

    all_offerings = []

    for year in range(start_year, end_year + 1):
        start_date = f"{year}0101"
        end_date = f"{year}1231"

        logger.info(f"Fetching IPO offerings for {year}...")

        try:
            offerings = client.get_ipo_offering_info(
                start_date=start_date,
                end_date=end_date,
                stock_code="",  # Get all stocks
            )

            logger.info(f"  Retrieved {len(offerings)} offerings for {year}")
            all_offerings.extend(offerings)

        except Exception as e:
            logger.error(f"Failed to fetch offerings for {year}: {e}")

    if not all_offerings:
        logger.warning("No IPO offerings retrieved")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_offerings)

    logger.info(f"Total offerings collected: {len(df)}")

    return df


def clean_and_filter_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and filter IPO offering data

    Args:
        df: Raw offering data

    Returns:
        Cleaned DataFrame with essential columns
    """
    if df.empty:
        return df

    logger.info("Cleaning IPO offering data...")

    # Select essential columns (adjust based on actual API response)
    essential_cols = {
        "sht_cd": "code",
        "fix_subscr_pri": "ipo_price",
        "face_value": "par_value",
        "list_dt": "listing_date",
        "subscr_dt": "subscription_period",
        "pay_dt": "payment_date",
        "refund_dt": "refund_date",
        "lead_mgr": "lead_manager",
    }

    # Keep only columns that exist in the response
    available_cols = {k: v for k, v in essential_cols.items() if k in df.columns}

    if not available_cols:
        logger.error("No expected columns found in API response")
        logger.info(f"Available columns: {df.columns.tolist()}")
        return df

    df_clean = df[list(available_cols.keys())].copy()
    df_clean = df_clean.rename(columns=available_cols)

    # Convert numeric columns
    if "ipo_price" in df_clean.columns:
        df_clean["ipo_price"] = pd.to_numeric(df_clean["ipo_price"], errors="coerce")

    if "par_value" in df_clean.columns:
        df_clean["par_value"] = pd.to_numeric(df_clean["par_value"], errors="coerce")

    # Convert code to string and pad with zeros
    if "code" in df_clean.columns:
        df_clean["code"] = df_clean["code"].astype(str).str.zfill(6)

    # Remove rows without IPO price
    if "ipo_price" in df_clean.columns:
        before = len(df_clean)
        df_clean = df_clean[df_clean["ipo_price"].notna()]
        after = len(df_clean)

        if before > after:
            logger.info(f"Removed {before - after} rows without IPO price")

    logger.info(f"Cleaned data: {len(df_clean)} records")

    return df_clean


def main():
    """Collect and save IPO offering prices"""
    print("=" * 80)
    print("COLLECTING IPO OFFERING PRICES FROM KIS API")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Define date range
    start_year = settings.DATA_START_YEAR
    end_year = settings.DATA_END_YEAR

    print(f"Date range: {start_year} - {end_year}")
    print()

    # Collect data
    print("=" * 80)
    print("FETCHING DATA FROM KIS API")
    print("=" * 80)

    df_raw = collect_ipo_offering_data(start_year, end_year)

    if df_raw.empty:
        print("❌ No data collected")
        return

    print(f"✅ Collected {len(df_raw)} total records")
    print()

    # Clean data
    print("=" * 80)
    print("CLEANING DATA")
    print("=" * 80)

    df_clean = clean_and_filter_data(df_raw)

    if df_clean.empty:
        print("❌ No data after cleaning")
        print("\nRaw data columns:")
        print(df_raw.columns.tolist())
        print("\nSample raw data:")
        print(df_raw.head())
        return

    print(f"✅ {len(df_clean)} records after cleaning")
    print()

    # Show sample
    print("=" * 80)
    print("SAMPLE DATA (첫 10개)")
    print("=" * 80)
    print(df_clean.head(10))
    print()

    # Save to CSV
    print("=" * 80)
    print("SAVING DATA")
    print("=" * 80)

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "ipo_offering_info.csv"
    df_clean.to_csv(output_file, index=False, encoding="utf-8-sig")

    file_size = output_file.stat().st_size / 1024  # KB

    print(f"✅ Saved to: {output_file}")
    print(f"   File size: {file_size:.2f} KB")
    print(f"   Records: {len(df_clean)}")
    print()

    # Statistics
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)

    if "ipo_price" in df_clean.columns:
        print(f"IPO Price statistics:")
        print(f"  Min:    {df_clean['ipo_price'].min():>12,.0f}원")
        print(f"  Max:    {df_clean['ipo_price'].max():>12,.0f}원")
        print(f"  Mean:   {df_clean['ipo_price'].mean():>12,.0f}원")
        print(f"  Median: {df_clean['ipo_price'].median():>12,.0f}원")

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
