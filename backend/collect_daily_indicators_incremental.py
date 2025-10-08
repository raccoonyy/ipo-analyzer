"""
Collect Daily Indicators Incrementally
Only collect KIS API data for new IPOs
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
from tqdm import tqdm
from src.api.kis_client import KISApiClient
from src.config.settings import settings
from src.utils.last_run_tracker import LastRunTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def parse_daily_data(daily_record: dict) -> dict:
    """Parse daily data from KIS API response"""
    return {
        "date": daily_record.get("stck_bsop_date", ""),
        "close": float(daily_record.get("stck_clpr", 0)),
        "open": float(daily_record.get("stck_oprc", 0)),
        "high": float(daily_record.get("stck_hgpr", 0)),
        "low": float(daily_record.get("stck_lwpr", 0)),
        "volume": int(daily_record.get("acml_vol", 0)),
        "trading_value": float(daily_record.get("acml_tr_pbmn", 0)),
        "market_cap": float(daily_record.get("hts_avls", 0)),
        "per": float(daily_record.get("per", 0)),
        "pbr": float(daily_record.get("pbr", 0)),
        "eps": float(daily_record.get("eps", 0)),
        "listed_shares": float(daily_record.get("lstn_stcn", 0)),
    }


def collect_ipo_daily_indicators(
    client: KISApiClient,
    stock_code: str,
    listing_date: str,
    company_name: str,
) -> pd.DataFrame:
    """Collect daily indicators for a single IPO"""
    logger.info(f"Collecting daily indicators for {company_name} ({stock_code})...")

    date_obj = pd.to_datetime(listing_date)
    start_date = date_obj.strftime("%Y%m%d")
    end_date = (date_obj + timedelta(days=5)).strftime("%Y%m%d")

    try:
        daily_records = client.get_daily_ohlcv(stock_code, start_date, end_date)

        if not daily_records:
            logger.warning(f"No data retrieved for {company_name}")
            return pd.DataFrame()

        parsed_records = [parse_daily_data(r) for r in daily_records]
        df = pd.DataFrame(parsed_records)
        df = df[df["date"] != ""]

        if df.empty:
            logger.warning(f"No valid data for {company_name} after filtering")
            return pd.DataFrame()

        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
        df = df.dropna(subset=["date"])
        df = df.sort_values("date")

        df["company_name"] = company_name
        df["code"] = stock_code
        df["listing_date"] = listing_date
        df = df.head(2)

        logger.info(f"✅ Collected {len(df)} trading days for {company_name}")
        return df

    except Exception as e:
        logger.error(f"Failed to collect data for {company_name}: {e}")
        return pd.DataFrame()


def main():
    """Collect daily indicators incrementally"""
    print("=" * 80)
    print("INCREMENTAL DAILY INDICATORS COLLECTION (KIS API)")
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

    # Initialize tracker
    tracker = LastRunTracker()
    script_name = "collect_daily_indicators"

    # Load main IPO dataset
    input_file = f"data/raw/ipo_full_dataset_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}.csv"
    df_ipos = pd.read_csv(input_file)
    df_ipos["listing_date"] = pd.to_datetime(df_ipos["listing_date"])

    # Get last run date
    last_run = tracker.get_last_run(script_name)

    if last_run:
        print("=" * 80)
        print("INCREMENTAL UPDATE MODE")
        print("=" * 80)
        print(f"Last collection: {last_run}")
        print()

        # Filter to only new IPOs
        df_new_ipos = df_ipos[df_ipos["listing_date"] > pd.to_datetime(last_run)]

        if len(df_new_ipos) == 0:
            print("No new IPOs found since last run.")
            print()
            return
    else:
        print("=" * 80)
        print("INITIAL COLLECTION MODE")
        print("=" * 80)
        print("Collecting for all IPOs")
        print()
        df_new_ipos = df_ipos

    print(f"IPOs to process: {len(df_new_ipos)}")
    print(f"Date range: {df_new_ipos['listing_date'].min()} to {df_new_ipos['listing_date'].max()}")
    print()

    # Initialize KIS client
    client = KISApiClient()

    print("Authenticating with KIS API...")
    try:
        token = client.authenticate()
        print(f"✅ Authentication successful")
        print(f"   Token expires at: {client.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    print()

    # Collect data
    print("=" * 80)
    print("COLLECTING DAILY INDICATORS")
    print("=" * 80)
    print(f"Rate limit: 1 request per second")
    print(f"Estimated time: ~{len(df_new_ipos)} seconds ({len(df_new_ipos)/60:.1f} minutes)")
    print()

    all_daily_data = []
    success_count = 0
    failed_count = 0

    for idx, row in tqdm(df_new_ipos.iterrows(), total=len(df_new_ipos), desc="Processing IPOs"):
        stock_code = str(row["code"]).zfill(6)
        listing_date = row["listing_date"].strftime("%Y-%m-%d")
        company_name = row["company_name"]

        df_daily = collect_ipo_daily_indicators(
            client, stock_code, listing_date, company_name
        )

        if not df_daily.empty:
            all_daily_data.append(df_daily)
            success_count += 1
        else:
            failed_count += 1

        time.sleep(1.0)

    print()
    print("=" * 80)
    print("COLLECTION SUMMARY")
    print("=" * 80)
    print(f"Total IPOs: {len(df_new_ipos)}")
    print(f"Successful: {success_count} ({success_count/len(df_new_ipos)*100:.1f}%)")
    print(f"Failed: {failed_count} ({failed_count/len(df_new_ipos)*100:.1f}%)")
    print()

    # Combine and save
    if all_daily_data:
        print("=" * 80)
        print("SAVING DATA")
        print("=" * 80)

        df_new_combined = pd.concat(all_daily_data, ignore_index=True)

        # Load existing data if present
        output_dir = Path("data/raw/daily_indicators")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"ipo_daily_indicators_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}.csv"

        if output_file.exists() and last_run:
            print(f"Loading existing data from {output_file}...")
            df_existing = pd.read_csv(output_file)
            print(f"Existing records: {len(df_existing)}")
            print(f"New records: {len(df_new_combined)}")

            # Remove duplicates (just in case)
            existing_codes = set(df_existing["code"].astype(str))
            df_new_filtered = df_new_combined[~df_new_combined["code"].astype(str).isin(existing_codes)]

            if len(df_new_filtered) < len(df_new_combined):
                print(f"Filtered out {len(df_new_combined) - len(df_new_filtered)} duplicates")

            df_combined = pd.concat([df_existing, df_new_filtered], ignore_index=True)
            print(f"Total records after merge: {len(df_combined)}")
        else:
            df_combined = df_new_combined
            print(f"Creating new file with {len(df_combined)} records")

        # Save
        df_combined.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"✅ Saved to: {output_file}")
        print(f"   Total records: {len(df_combined):,}")
        print()

        # Update tracker
        tracker.update_last_run(script_name)

        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print("Run the following to update the full pipeline:")
        print("  1. uv run python merge_indicators.py          (merge into enhanced dataset)")
        print("  2. uv run python train_model.py               (retrain model)")
        print("  3. uv run python generate_frontend_predictions.py  (update frontend)")
        print()

    print("=" * 80)
    print("INCREMENTAL COLLECTION COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
