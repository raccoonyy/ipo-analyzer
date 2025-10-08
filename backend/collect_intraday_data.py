"""
Collect Intraday Data for IPOs
Fetches minute-level price data for complete IPO dataset using KIS API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
from tqdm import tqdm
from src.api.kis_client import KISApiClient
from src.config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def parse_minute_candle(candle_data: dict) -> dict:
    """
    Parse minute candle data from KIS API response

    Args:
        candle_data: Raw candle data from API

    Returns:
        Parsed candle dictionary
    """
    # stck_cntg_hour format: YYYYMMDDHHMM (e.g., "202410071530")
    time_str = candle_data.get("stck_cntg_hour", "")

    # Extract date and time separately
    if len(time_str) >= 12:
        date_part = time_str[:8]  # YYYYMMDD
        time_part = time_str[8:12]  # HHMM
    else:
        date_part = ""
        time_part = ""

    return {
        "date": date_part,
        "time": time_part,
        "datetime_str": time_str,
        "open": float(candle_data.get("stck_oprc", 0)),
        "high": float(candle_data.get("stck_hgpr", 0)),
        "low": float(candle_data.get("stck_lwpr", 0)),
        "close": float(candle_data.get("stck_prpr", 0)),
        "volume": int(candle_data.get("cntg_vol", 0)),
        "value": float(candle_data.get("acml_tr_pbmn", 0)),  # Accumulated trade value
    }


def collect_ipo_intraday(
    client: KISApiClient, stock_code: str, listing_date: str, company_name: str
) -> pd.DataFrame:
    """
    Collect intraday data for a single IPO

    Args:
        client: KIS API client
        stock_code: 6-digit stock code
        listing_date: Listing date in YYYY-MM-DD format
        company_name: Company name for logging

    Returns:
        DataFrame with intraday data
    """
    logger.info(f"Collecting intraday data for {company_name} ({stock_code})...")

    # Convert listing date to YYYYMMDD format
    date_obj = pd.to_datetime(listing_date)
    date_str = date_obj.strftime("%Y%m%d")

    # Fetch minute candles
    try:
        candles = client.get_minute_candles(stock_code, date_str, interval="1")

        if not candles:
            logger.warning(f"No data retrieved for {company_name}")
            return pd.DataFrame()

        # Parse candles
        parsed_candles = [parse_minute_candle(c) for c in candles]

        # Create DataFrame
        df = pd.DataFrame(parsed_candles)

        # Filter out empty records
        df = df[df["datetime_str"] != ""]

        if df.empty:
            logger.warning(f"No valid data for {company_name} after filtering")
            return pd.DataFrame()

        # Add metadata
        df["company_name"] = company_name
        df["code"] = stock_code
        df["listing_date"] = listing_date

        # Parse datetime - handle 12-digit format YYYYMMDDHHMM
        df["datetime"] = pd.to_datetime(df["datetime_str"], format="%Y%m%d%H%M", errors="coerce")

        # Drop rows with invalid datetime
        df = df.dropna(subset=["datetime"])

        # Sort by time
        df = df.sort_values("datetime")

        logger.info(
            f"✅ Collected {len(df)} minute candles for {company_name} on {listing_date}"
        )

        return df

    except Exception as e:
        logger.error(f"Failed to collect data for {company_name}: {e}")
        return pd.DataFrame()


def main():
    """Collect intraday data for all complete IPOs"""
    print("=" * 80)
    print("IPO INTRADAY DATA COLLECTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check API credentials
    if not settings.KIS_APP_KEY or not settings.KIS_APP_SECRET:
        print("❌ KIS_APP_KEY and KIS_APP_SECRET not found in .env file")
        print("Please set these values before running.")
        return

    print(f"✅ API credentials configured")
    print()

    # Load complete IPO dataset
    input_file = "data/raw/ipo_full_dataset_2022_2024_complete.csv"
    df_ipos = pd.read_csv(input_file)

    print(f"Loaded {len(df_ipos)} complete IPO records")
    print(f"Date range: {df_ipos['listing_date'].min()} to {df_ipos['listing_date'].max()}")
    print()

    # Initialize KIS client
    client = KISApiClient()

    # Pre-authenticate once at the start
    print("Authenticating with KIS API...")
    try:
        token = client.authenticate()
        print(f"✅ Authentication successful")
        print(f"   Token expires at: {client.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    print()

    # Prepare output directory
    output_dir = Path("data/raw/intraday")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect data for each IPO
    print("=" * 80)
    print("COLLECTING INTRADAY DATA")
    print("=" * 80)
    print(f"Rate limit: 1 request per second")
    print(f"Estimated time: ~{len(df_ipos)} seconds ({len(df_ipos)/60:.1f} minutes)")
    print()

    all_intraday_data = []
    success_count = 0
    failed_count = 0

    for idx, row in tqdm(df_ipos.iterrows(), total=len(df_ipos), desc="Processing IPOs"):
        stock_code = str(row["code"]).zfill(6)  # Ensure 6 digits
        listing_date = row["listing_date"]
        company_name = row["company_name"]

        # Collect intraday data
        df_intraday = collect_ipo_intraday(
            client, stock_code, listing_date, company_name
        )

        if not df_intraday.empty:
            all_intraday_data.append(df_intraday)
            success_count += 1
        else:
            failed_count += 1

        # Rate limiting: KIS API has rate limits
        # Wait 1 second between requests to avoid hitting limits
        time.sleep(1.0)

    print()
    print("=" * 80)
    print("COLLECTION SUMMARY")
    print("=" * 80)
    print(f"Total IPOs: {len(df_ipos)}")
    print(f"Successful: {success_count} ({success_count/len(df_ipos)*100:.1f}%)")
    print(f"Failed: {failed_count} ({failed_count/len(df_ipos)*100:.1f}%)")
    print()

    # Combine all data
    if all_intraday_data:
        print("=" * 80)
        print("SAVING DATA")
        print("=" * 80)

        df_combined = pd.concat(all_intraday_data, ignore_index=True)

        # Save combined dataset
        output_file = output_dir / "ipo_intraday_2022_2024.csv"
        df_combined.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f"✅ Saved combined intraday data: {output_file}")
        print(f"   Total records: {len(df_combined):,}")
        print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        print()

        # Show statistics
        print("=" * 80)
        print("DATA STATISTICS")
        print("=" * 80)

        avg_candles = len(df_combined) / success_count if success_count > 0 else 0
        print(f"Average candles per IPO: {avg_candles:.1f}")
        print()

        # Show sample
        print("Sample data (first 5 records):")
        print(
            df_combined[
                ["company_name", "code", "datetime", "open", "high", "low", "close", "volume"]
            ]
            .head()
            .to_string()
        )
        print()

    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
