"""Collect KOSPI IPO data using yfinance"""
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

def get_listing_day_data(code, listing_date, market='KOSPI'):
    """
    Get Day 0 and Day 1 trading data using yfinance

    Args:
        code: Stock code (6 digits)
        listing_date: Listing date (YYYY-MM-DD format)
        market: 'KOSPI' or 'KOSDAQ'

    Returns:
        dict with day0_high, day0_close, day1_close, volumes
    """
    # Add market suffix
    ticker_suffix = '.KS' if market == 'KOSPI' else '.KQ'
    ticker = f"{code}{ticker_suffix}"

    # Parse listing date
    listing_dt = pd.to_datetime(listing_date)

    # Fetch data for 10 days after listing
    start_date = listing_dt
    end_date = listing_dt + timedelta(days=10)

    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start_date, end=end_date)

        if len(hist) == 0:
            print(f"  ✗ No data for {ticker}")
            return None

        # Get Day 0 (first trading day)
        day0 = hist.iloc[0]

        result = {
            'day0_high': day0['High'],
            'day0_close': day0['Close'],
            'day0_volume': day0['Volume'],
            'day0_open': day0['Open'],
            'day0_low': day0['Low'],
        }

        # Get Day 1 (second trading day) if available
        if len(hist) >= 2:
            day1 = hist.iloc[1]
            result['day1_close'] = day1['Close']
            result['day1_volume'] = day1['Volume']
            result['day1_high'] = day1['High']
            result['day1_low'] = day1['Low']
        else:
            result['day1_close'] = None
            result['day1_volume'] = None
            result['day1_high'] = None
            result['day1_low'] = None

        return result

    except Exception as e:
        print(f"  ✗ Error for {ticker}: {e}")
        return None


def main():
    print("="*80)
    print("COLLECTING KOSPI IPO DATA FROM YFINANCE")
    print("="*80)
    print()

    # Load market classification
    df_market = pd.read_csv('data/raw/38_market_classification.csv')

    # Normalize
    df_market['listing_method'] = df_market['listing_method'].replace({'코스피': 'KOSPI'})

    # Filter KOSPI only
    df_kospi = df_market[df_market['listing_method'] == 'KOSPI'].copy()

    print(f"Found {len(df_kospi)} KOSPI IPOs")
    print()

    # Need listing dates - merge with subscription data
    df_sub = pd.read_csv('data/raw/38_subscription_data.csv')
    df_kospi = df_kospi.merge(df_sub[['code', 'listing_date']], on='code', how='left')

    # Remove rows without listing date
    df_kospi = df_kospi[df_kospi['listing_date'].notna()].copy()

    print(f"KOSPI IPOs with listing dates: {len(df_kospi)}")
    print()

    # Collect data
    results = []

    for idx, row in df_kospi.iterrows():
        code = str(row['code']).zfill(6)
        company_name = row['company_name']
        listing_date = row['listing_date']

        print(f"[{idx+1}/{len(df_kospi)}] {company_name} ({code}) - {listing_date}...", end=' ')

        data = get_listing_day_data(code, listing_date, market='KOSPI')

        if data:
            print(f"✓ Day0: {data['day0_close']:.0f}, Day1: {data.get('day1_close', 'N/A')}")
            results.append({
                'code': code,
                'company_name': company_name,
                'listing_date': listing_date,
                **data
            })

        # Rate limit
        time.sleep(0.5)

    # Create DataFrame
    df_results = pd.DataFrame(results)

    # Summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total KOSPI IPOs: {len(df_kospi)}")
    print(f"Successfully collected: {len(df_results)}")
    print(f"Success rate: {len(df_results)/len(df_kospi)*100:.1f}%")
    print()

    # Save
    output_file = 'data/raw/kospi_ipo_yfinance.csv'
    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Saved to: {output_file}")
    print()

    # Show sample
    print("Sample data:")
    print(df_results[['company_name', 'listing_date', 'day0_high', 'day0_close', 'day1_close']].head(10))


if __name__ == '__main__':
    main()
