"""
Collect Daily Indicators for IPOs using KIS API
Fetches PER, EPS, PBR, trading volume metrics for listing day and day+1
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


def parse_daily_data(daily_record: dict) -> dict:
    """
    Parse daily data from KIS API response

    Args:
        daily_record: Raw daily data from API

    Returns:
        Parsed dictionary with all indicators
    """
    return {
        "date": daily_record.get("stck_bsop_date", ""),  # 영업일자
        "close": float(daily_record.get("stck_clpr", 0)),  # 종가
        "open": float(daily_record.get("stck_oprc", 0)),  # 시가
        "high": float(daily_record.get("stck_hgpr", 0)),  # 고가
        "low": float(daily_record.get("stck_lwpr", 0)),  # 저가
        "volume": int(daily_record.get("acml_vol", 0)),  # 누적거래량
        "trading_value": float(daily_record.get("acml_tr_pbmn", 0)),  # 누적거래대금
        "market_cap": float(daily_record.get("hts_avls", 0)),  # 시가총액
        "per": float(daily_record.get("per", 0)),  # PER
        "pbr": float(daily_record.get("pbr", 0)),  # PBR
        "eps": float(daily_record.get("eps", 0)),  # EPS
        "listed_shares": float(daily_record.get("lstn_stcn", 0)),  # 상장주수
    }


def collect_ipo_daily_indicators(
    client: KISApiClient,
    stock_code: str,
    listing_date: str,
    company_name: str,
) -> pd.DataFrame:
    """
    Collect daily indicators for a single IPO (listing day + day 1)

    Args:
        client: KIS API client
        stock_code: 6-digit stock code
        listing_date: Listing date in YYYY-MM-DD format
        company_name: Company name for logging

    Returns:
        DataFrame with daily indicators
    """
    logger.info(f"Collecting daily indicators for {company_name} ({stock_code})...")

    # Convert listing date to YYYYMMDD format
    date_obj = pd.to_datetime(listing_date)
    start_date = date_obj.strftime("%Y%m%d")

    # End date = listing date + 5 days (to ensure we get day 1 even with weekends)
    end_date = (date_obj + timedelta(days=5)).strftime("%Y%m%d")

    # Fetch daily data
    try:
        daily_records = client.get_daily_ohlcv(stock_code, start_date, end_date)

        if not daily_records:
            logger.warning(f"No data retrieved for {company_name}")
            return pd.DataFrame()

        # Parse records
        parsed_records = [parse_daily_data(r) for r in daily_records]

        # Create DataFrame
        df = pd.DataFrame(parsed_records)

        # Filter out empty records
        df = df[df["date"] != ""]

        if df.empty:
            logger.warning(f"No valid data for {company_name} after filtering")
            return pd.DataFrame()

        # Parse date
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
        df = df.dropna(subset=["date"])

        # Sort by date
        df = df.sort_values("date")

        # Add metadata
        df["company_name"] = company_name
        df["code"] = stock_code
        df["listing_date"] = listing_date

        # Filter to only listing day and next trading day
        # Get first 2 records (day 0 and day 1)
        df = df.head(2)

        logger.info(f"✅ Collected {len(df)} trading days for {company_name}")

        return df

    except Exception as e:
        logger.error(f"Failed to collect data for {company_name}: {e}")
        return pd.DataFrame()


def main():
    """Collect daily indicators for all complete IPOs"""
    print("=" * 80)
    print("IPO DAILY INDICATORS COLLECTION (KIS API)")
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
    output_dir = Path("data/raw/daily_indicators")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect data for each IPO
    print("=" * 80)
    print("COLLECTING DAILY INDICATORS")
    print("=" * 80)
    print(f"Rate limit: 1 request per second")
    print(f"Estimated time: ~{len(df_ipos)} seconds ({len(df_ipos)/60:.1f} minutes)")
    print()

    all_daily_data = []
    success_count = 0
    failed_count = 0

    for idx, row in tqdm(df_ipos.iterrows(), total=len(df_ipos), desc="Processing IPOs"):
        stock_code = str(row["code"]).zfill(6)  # Ensure 6 digits
        listing_date = row["listing_date"]
        company_name = row["company_name"]

        # Collect daily indicators
        df_daily = collect_ipo_daily_indicators(
            client, stock_code, listing_date, company_name
        )

        if not df_daily.empty:
            all_daily_data.append(df_daily)
            success_count += 1
        else:
            failed_count += 1

        # Rate limiting
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
    if all_daily_data:
        print("=" * 80)
        print("SAVING DATA")
        print("=" * 80)

        df_combined = pd.concat(all_daily_data, ignore_index=True)

        # Save combined dataset
        output_file = output_dir / "ipo_daily_indicators_2022_2024.csv"
        df_combined.to_csv(output_file, index=False, encoding="utf-8-sig")

        print(f"✅ Saved daily indicators: {output_file}")
        print(f"   Total records: {len(df_combined):,}")
        print(f"   File size: {output_file.stat().st_size / 1024:.2f} KB")
        print()

        # Show statistics
        print("=" * 80)
        print("DATA STATISTICS")
        print("=" * 80)

        avg_days = len(df_combined) / success_count if success_count > 0 else 0
        print(f"Average trading days per IPO: {avg_days:.1f}")
        print()

        # Show sample
        print("Sample data (first 5 records):")
        print(
            df_combined[
                ["company_name", "code", "date", "close", "volume", "per", "pbr", "eps"]
            ]
            .head()
            .to_string()
        )
        print()

        # Show indicator statistics
        print("=" * 80)
        print("INDICATOR STATISTICS")
        print("=" * 80)

        indicators = ["per", "pbr", "eps", "volume", "trading_value", "market_cap"]
        for indicator in indicators:
            valid_count = (df_combined[indicator] > 0).sum()
            print(f"{indicator:20}: {valid_count}/{len(df_combined)} ({valid_count/len(df_combined)*100:.1f}%) non-zero")

    print()
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
