"""
Collect Incremental IPO Data
Only collect new IPOs since last run
"""

from src.data_collection.ipo_collector import IPODataCollector
from src.utils.last_run_tracker import LastRunTracker
from src.config.settings import settings
import logging
from datetime import datetime, date
import pandas as pd
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Collect incremental IPO data"""
    print("=" * 80)
    print("INCREMENTAL IPO DATA COLLECTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not settings.KRX_API_KEY:
        print("❌ KRX_API_KEY not found in .env file")
        print("Please set KRX_API_KEY before running.")
        return

    print(f"✅ API Key configured: {settings.KRX_API_KEY[:10]}...")
    print()

    # Initialize tracker
    tracker = LastRunTracker()
    script_name = "collect_full_data"

    # Get date range
    start_date, end_date = tracker.get_collection_date_range(
        script_name,
        default_start_date=date(settings.DATA_START_YEAR, 1, 1)
    )

    print("=" * 80)
    print("COLLECTION RANGE")
    print("=" * 80)

    last_run = tracker.get_last_run(script_name)
    if last_run:
        print(f"Last collection: {last_run}")
        print(f"Collection mode: INCREMENTAL UPDATE")
        print(f"Date range: {start_date} to {end_date}")

        # Check if already up to date
        if start_date >= end_date:
            print()
            print("=" * 80)
            print("ALREADY UP TO DATE")
            print("=" * 80)
            print(f"Last run was on {last_run}, no new data to collect.")
            print()
            return
    else:
        print(f"Collection mode: INITIAL FULL COLLECTION")
        print(f"Date range: {start_date} to {end_date}")

    print()

    # Initialize collector
    collector = IPODataCollector(use_sample_data=False)

    try:
        # Collect data for date range
        print("=" * 80)
        print("COLLECTING DATA")
        print("=" * 80)
        print()

        # Convert dates to year range
        start_year = start_date.year
        end_year = end_date.year

        new_df = collector.collect_full_dataset(
            start_year=start_year,
            end_year=end_year,
            optimized=True,
        )

        # Filter to only new data (after last run)
        if last_run:
            new_df["listing_date"] = pd.to_datetime(new_df["listing_date"])
            new_df = new_df[new_df["listing_date"] > pd.to_datetime(last_run)]

        print()
        print("=" * 80)
        print(f"COLLECTED {len(new_df)} NEW IPOs")
        print("=" * 80)

        if len(new_df) == 0:
            print("No new IPOs found in the date range.")
            print()
            # Still update last run
            tracker.update_last_run(script_name)
            return

        print()
        print("New IPOs:")
        for idx, row in new_df.iterrows():
            print(f"  - {row['company_name']:30} ({row['code']}) : {row['listing_date']}")

        print()

        # Load existing data and merge
        main_file = Path(f"data/raw/ipo_full_dataset_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}.csv")

        if main_file.exists():
            print("=" * 80)
            print("MERGING WITH EXISTING DATA")
            print("=" * 80)

            existing_df = pd.read_csv(main_file)
            print(f"Existing records: {len(existing_df)}")
            print(f"New records: {len(new_df)}")

            # Merge (avoid duplicates)
            existing_codes = set(existing_df["code"].astype(str))
            new_df_filtered = new_df[~new_df["code"].astype(str).isin(existing_codes)]

            if len(new_df_filtered) < len(new_df):
                print(f"Filtered out {len(new_df) - len(new_df_filtered)} duplicates")

            combined_df = pd.concat([existing_df, new_df_filtered], ignore_index=True)

            # Sort by listing date
            combined_df["listing_date"] = pd.to_datetime(combined_df["listing_date"])
            combined_df = combined_df.sort_values("listing_date")
            combined_df["listing_date"] = combined_df["listing_date"].dt.strftime("%Y-%m-%d")

            print(f"Total records after merge: {len(combined_df)}")
            print()

        else:
            print("=" * 80)
            print("CREATING NEW DATASET FILE")
            print("=" * 80)
            print(f"This is the first collection, creating {main_file}")
            print()
            combined_df = new_df

        # Save merged data
        combined_df.to_csv(main_file, index=False, encoding="utf-8-sig")
        print(f"✅ Saved to: {main_file}")
        print()

        # Also update enhanced dataset if exists
        enhanced_file = Path(f"data/raw/ipo_full_dataset_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}_enhanced.csv")

        if enhanced_file.exists() and len(new_df) > 0:
            print("=" * 80)
            print("NOTE: Enhanced dataset exists")
            print("=" * 80)
            print(f"You need to run the following to update enhanced dataset:")
            print(f"  1. uv run python collect_daily_indicators.py  (collect KIS data for new IPOs)")
            print(f"  2. uv run python merge_indicators.py          (merge into enhanced dataset)")
            print(f"  3. uv run python train_model.py               (retrain model)")
            print(f"  4. uv run python generate_frontend_predictions.py  (update frontend)")
            print()

        # Update tracker
        tracker.update_last_run(script_name, end_date)

        # Show API usage
        if hasattr(collector, "krx_client"):
            stats = collector.krx_client.get_request_stats()
            print("=" * 80)
            print("API USAGE STATISTICS")
            print("=" * 80)
            total_requests = 0
            for api_name, count in stats.items():
                pct = (count / 10000) * 100
                print(f"{api_name:15} : {count:5,} / 10,000 ({pct:5.2f}%)")
                total_requests += count

            print("-" * 80)
            print(f"{'Total':15} : {total_requests:5,} / 20,000 ({(total_requests/20000)*100:5.2f}%)")

        print()
        print("=" * 80)
        print("INCREMENTAL UPDATE COMPLETE")
        print("=" * 80)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Next run will collect data from {end_date} onwards")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR OCCURRED")
        print("=" * 80)
        print(f"Error: {e}")
        print()

        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
