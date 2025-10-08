"""
Collect 2025 IPO data from KRX API
"""

import sys
import time
from datetime import datetime
import pandas as pd
from src.data_collection.ipo_collector import IPODataCollector
from src.config.settings import settings

def main():
    print("=" * 80)
    print("2025 IPO DATA COLLECTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not settings.KRX_API_KEY:
        print("❌ KRX_API_KEY not found in .env file")
        print("Please set KRX_API_KEY before running.")
        return

    print(f"✅ API Key configured: {settings.KRX_API_KEY[:10]}...")
    print()

    # Initialize collector
    collector = IPODataCollector(use_sample_data=False)

    try:
        # Collect 2025 IPO data
        print("=" * 80)
        print("Starting data collection for 2025...")
        print("=" * 80)
        print()

        df_2025 = collector.collect_full_dataset(
            start_year=2025,
            end_year=2025,
            optimized=True,
        )

        print()
        print("=" * 80)
        print("COLLECTION COMPLETE")
        print("=" * 80)
        print(f"Total 2025 IPOs collected: {len(df_2025)}")
        print()

        # Save dataset
        output_file = "data/raw/ipo_2025_dataset.csv"
        df_2025.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✅ Saved to: {output_file}")
        print()

        # Show statistics
        print("=" * 80)
        print("STATISTICS")
        print("=" * 80)
        print(f"Date range: {df_2025['listing_date'].min()} to {df_2025['listing_date'].max()}")

        # Check data completeness
        has_prices = (
            (df_2025["day0_high"] > 0)
            & (df_2025["day0_close"] > 0)
        )
        complete_count = has_prices.sum()
        print(f"\nData completeness:")
        print(f"  Complete records: {complete_count}/{len(df_2025)} ({complete_count/len(df_2025)*100:.1f}%)")

        print(f"\nIndustry distribution:")
        industry_counts = df_2025['industry'].value_counts()
        for industry, count in industry_counts.head(10).items():
            print(f"  {industry:40}: {count}")

        print()
        print("Sample records (first 10):")
        print("-" * 80)
        cols_to_show = ['company_name', 'code', 'listing_date', 'ipo_price_confirmed', 'day0_high', 'day0_close', 'day1_close']
        print(df_2025[cols_to_show].head(10).to_string())

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

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
