"""
Collect Full IPO Data (2022-2025)
Uses optimized collection with caching and progress monitoring
"""

from src.data_collection.ipo_collector import IPODataCollector
from src.config.settings import settings
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Collect full IPO dataset for 2022-2025"""
    print("=" * 80)
    print("IPO DATA COLLECTION (2022-2025)")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not settings.KRX_API_KEY:
        print("❌ KRX_API_KEY not found in .env file")
        print("Please set KRX_API_KEY before running.")
        return

    print(f"✅ API Key configured: {settings.KRX_API_KEY[:10]}...")
    print(f"✅ Data range: {settings.DATA_START_YEAR} - {settings.DATA_END_YEAR}")
    print()

    # Initialize collector
    collector = IPODataCollector(use_sample_data=False)

    try:
        # Collect full dataset with optimization
        print("=" * 80)
        print("Starting optimized data collection...")
        print("=" * 80)
        print()

        full_df = collector.collect_full_dataset(
            start_year=settings.DATA_START_YEAR,
            end_year=settings.DATA_END_YEAR,
            optimized=True,
        )

        print()
        print("=" * 80)
        print("COLLECTION COMPLETE")
        print("=" * 80)
        print(f"Total IPOs collected: {len(full_df)}")
        print(
            f"Output file: data/raw/ipo_full_dataset_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}.csv"
        )

        # Show API usage
        if hasattr(collector, "krx_client"):
            stats = collector.krx_client.get_request_stats()
            print()
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
            print(f"{'Remaining':15} : {20000 - total_requests:5,} requests")

        # Data quality check
        print()
        print("=" * 80)
        print("DATA QUALITY CHECK")
        print("=" * 80)

        # Check for missing prices
        has_prices = (
            (full_df["day0_high"] > 0)
            & (full_df["day0_close"] > 0)
            & (full_df["day1_close"] > 0)
        )
        complete_count = has_prices.sum()
        missing_count = len(full_df) - complete_count

        print(f"Total IPOs:          {len(full_df):5}")
        print(f"Complete data:       {complete_count:5} ({complete_count/len(full_df)*100:.1f}%)")
        print(f"Incomplete data:     {missing_count:5} ({missing_count/len(full_df)*100:.1f}%)")

        if missing_count > 0:
            print()
            print(f"Note: {missing_count} IPOs have incomplete price data.")
            print(
                "This may be due to weekends/holidays following listing date,"
            )
            print("or stocks that were delisted shortly after IPO.")

        # Show summary by year
        print()
        print("=" * 80)
        print("SUMMARY BY YEAR")
        print("=" * 80)

        for year in range(settings.DATA_START_YEAR, settings.DATA_END_YEAR + 1):
            year_df = full_df[full_df["listing_date"].str.startswith(str(year))]
            year_complete = (
                (year_df["day0_high"] > 0)
                & (year_df["day0_close"] > 0)
                & (year_df["day1_close"] > 0)
            ).sum()

            print(
                f"{year}: {len(year_df):4} IPOs "
                f"({year_complete} complete, {len(year_df) - year_complete} incomplete)"
            )

        # Show sample data
        print()
        print("=" * 80)
        print("SAMPLE DATA (First 10 IPOs)")
        print("=" * 80)
        print()
        print(
            full_df[
                [
                    "company_name",
                    "code",
                    "listing_date",
                    "day0_high",
                    "day0_close",
                    "day1_close",
                ]
            ]
            .head(10)
            .to_string()
        )

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(
            f"Data saved to: data/raw/ipo_full_dataset_{settings.DATA_START_YEAR}_{settings.DATA_END_YEAR}.csv"
        )
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

        print()
        print("You can resume collection by running this script again.")
        print("Completed data is cached and will not be re-fetched.")


if __name__ == "__main__":
    main()
