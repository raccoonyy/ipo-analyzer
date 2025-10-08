"""
Collect 2025 IPO data from KIS API
"""

import pandas as pd
import time
from datetime import datetime, timedelta
from src.api.kis_client import KISApiClient
from src.config.settings import settings


def collect_2025_ipo_data():
    """Collect 2025 IPO data from KIS API"""

    print("=" * 80)
    print("2025 IPO DATA COLLECTION (KIS API)")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize KIS client
    client = KISApiClient()

    # Step 1: Get IPO offering information for 2025
    print("Step 1: Collecting IPO offering data for 2025...")
    print("-" * 80)

    offering_data = client.get_ipo_offering_info(
        start_date="20250101", end_date="20251231", stock_code=""
    )

    print(f"Total offerings found: {len(offering_data)}")
    print()

    if not offering_data:
        print("⚠️  No 2025 IPO data found from KIS API")
        return

    # Convert to DataFrame
    df_offering = pd.DataFrame(offering_data)

    # Show columns
    print("Available columns:")
    for i, col in enumerate(df_offering.columns, 1):
        print(f"  {i:2}. {col}")
    print()

    # Show sample
    print("Sample offerings (first 5):")
    print("-" * 80)
    print(df_offering.head().to_string())
    print()

    # Step 2: Filter IPOs with listing date
    print("Step 2: Filtering IPOs with listing dates...")
    print("-" * 80)

    # Filter IPOs that have listing dates (list_dt not empty)
    df_offering["list_dt"] = df_offering["list_dt"].str.strip()
    df_listed = df_offering[df_offering["list_dt"].notna() & (df_offering["list_dt"] != "")].copy()

    # Convert list_dt to datetime
    df_listed.loc[:, "listing_date"] = pd.to_datetime(
        df_listed["list_dt"], format="%Y/%m/%d", errors="coerce"
    )

    # Filter only IPOs that have already listed (listing_date <= today)
    today = pd.Timestamp.now()
    df_listed = df_listed[df_listed["listing_date"] <= today]

    print(f"IPOs with listing dates: {len(df_listed)}")
    print(f"Already listed (≤ today): {len(df_listed)}")
    print()

    if df_listed.empty:
        print("⚠️  No listed IPOs found yet")
        return

    # Step 3: Collect daily price data
    print("Step 3: Collecting daily price data for listed IPOs...")
    print("-" * 80)
    print("Note: Rate limit = 1 token request per minute")
    print()

    enhanced_ipos = []
    failed_ipos = []

    for idx, row in df_listed.iterrows():
        stock_code = row["sht_cd"].strip()
        company_name = row["isin_name"].strip()
        listing_date = row["listing_date"]
        listing_date_str = listing_date.strftime("%Y-%m-%d")

        print(
            f"[{idx+1}/{len(df_listed)}] {company_name} ({stock_code}) - {listing_date_str}"
        )

        try:
            # Get daily data (day0 and day1)
            start_date = listing_date.strftime("%Y%m%d")
            end_date = (listing_date + timedelta(days=5)).strftime("%Y%m%d")

            daily_records = client.get_daily_ohlcv(stock_code, start_date, end_date)

            if daily_records and len(daily_records) >= 1:
                # Parse day0 data
                day0 = daily_records[0]
                enhanced_row = {
                    "company_name": company_name,
                    "code": stock_code,
                    "listing_date": listing_date_str,
                    "ipo_price_confirmed": float(row["fix_subscr_pri"]),
                    "par_value": float(row["face_value"]),
                    "day0_open": float(day0.get("stck_oprc", 0)),
                    "day0_high": float(day0.get("stck_hgpr", 0)),
                    "day0_low": float(day0.get("stck_lwpr", 0)),
                    "day0_close": float(day0.get("stck_clpr", 0)),
                    "day0_volume": int(day0.get("acml_vol", 0)),
                    "day0_trading_value": float(day0.get("acml_tr_pbmn", 0)),
                }

                # Parse day1 data if available
                if len(daily_records) >= 2:
                    day1 = daily_records[1]
                    enhanced_row.update(
                        {
                            "day1_open": float(day1.get("stck_oprc", 0)),
                            "day1_high": float(day1.get("stck_hgpr", 0)),
                            "day1_low": float(day1.get("stck_lwpr", 0)),
                            "day1_close": float(day1.get("stck_clpr", 0)),
                            "day1_volume": int(day1.get("acml_vol", 0)),
                            "day1_trading_value": float(day1.get("acml_tr_pbmn", 0)),
                        }
                    )
                else:
                    enhanced_row.update(
                        {
                            "day1_open": 0,
                            "day1_high": 0,
                            "day1_low": 0,
                            "day1_close": 0,
                            "day1_volume": 0,
                            "day1_trading_value": 0,
                        }
                    )

                enhanced_ipos.append(enhanced_row)
                print(
                    f"  ✓ day0_close: {enhanced_row['day0_close']:,}원, day1_close: {enhanced_row['day1_close']:,}원"
                )

            else:
                failed_ipos.append(
                    {"company_name": company_name, "code": stock_code, "reason": "No price data"}
                )
                print(f"  ✗ No price data available")

        except Exception as e:
            failed_ipos.append(
                {"company_name": company_name, "code": stock_code, "reason": str(e)}
            )
            print(f"  ✗ Error: {e}")

        # Rate limit: wait 65 seconds between requests
        if idx < len(df_listed) - 1:
            print(f"  Waiting 65 seconds for API rate limit...")
            time.sleep(65)

        print()

    # Save results
    print("=" * 80)
    print("COLLECTION COMPLETE")
    print("=" * 80)
    print(f"Total 2025 IPOs: {len(df_offering)}")
    print(f"Listed IPOs: {len(df_listed)}")
    print(f"Successfully collected: {len(enhanced_ipos)}")
    print(f"Failed: {len(failed_ipos)}")
    print()

    if enhanced_ipos:
        # Save enhanced dataset
        df_enhanced = pd.DataFrame(enhanced_ipos)
        output_file = "data/raw/ipo_2025_dataset.csv"
        df_enhanced.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"✅ Saved to: {output_file}")
        print()

        # Show statistics
        print("STATISTICS:")
        print("-" * 80)
        print(
            f"Date range: {df_enhanced['listing_date'].min()} to {df_enhanced['listing_date'].max()}"
        )

        # Check data completeness
        has_prices = (df_enhanced["day0_high"] > 0) & (df_enhanced["day0_close"] > 0)
        complete_count = has_prices.sum()
        print(f"\nData completeness:")
        print(
            f"  Complete records: {complete_count}/{len(df_enhanced)} ({complete_count/len(df_enhanced)*100:.1f}%)"
        )

        print()
        print("Sample records (first 10):")
        print("-" * 80)
        cols_to_show = [
            "company_name",
            "code",
            "listing_date",
            "ipo_price_confirmed",
            "day0_close",
            "day1_close",
        ]
        print(df_enhanced[cols_to_show].head(10).to_string())

    if failed_ipos:
        print()
        print("Failed IPOs:")
        print("-" * 80)
        for ipo in failed_ipos:
            print(
                f"  - {ipo.get('company_name', 'N/A')} ({ipo.get('code', 'N/A')}): {ipo.get('reason', 'Unknown error')}"
            )


if __name__ == "__main__":
    collect_2025_ipo_data()
