"""Collect market classification (KOSDAQ vs KOSPI) from 38.co.kr"""
import pandas as pd
import subprocess
from bs4 import BeautifulSoup
import time
import re


def get_market_classification(ipo_no):
    """
    Fetch market classification for a given ipo_no from 38.co.kr

    Returns:
        'KOSPI' or 'KOSDAQ' or None
    """
    url = f"https://www.38.co.kr/html/fund/?o=v&no={ipo_no}"

    try:
        # Fetch with curl
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            timeout=10
        )

        # Decode with EUC-KR
        html = result.stdout.decode('euc-kr', errors='ignore')

        soup = BeautifulSoup(html, 'html.parser')

        # Find tables with market info
        tables = soup.find_all('table')
        for table in tables:
            text = table.get_text()

            # Look for "시장구분" row
            if '시장구분' in text:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text().strip()
                        value = cells[1].get_text().strip()

                        if label == '시장구분':
                            # Map Korean names to standard codes
                            if '거래소' in value or 'KOSPI' in value or '유가증권' in value:
                                return 'KOSPI'
                            elif '코스닥' in value or 'KOSDAQ' in value:
                                return 'KOSDAQ'
                            elif 'KONEX' in value or '코넥스' in value:
                                return 'KONEX'
                            else:
                                return value  # Return as-is if unknown

        return None

    except Exception as e:
        print(f"Error fetching ipo_no {ipo_no}: {e}")
        return None


def main():
    print("="*80)
    print("COLLECTING MARKET CLASSIFICATION FROM 38.CO.KR")
    print("="*80)
    print()

    # Load subscription data which has ipo_no
    df_sub = pd.read_csv('data/raw/38_subscription_data.csv')
    print(f"Loaded {len(df_sub)} IPOs from 38_subscription_data.csv")
    print()

    # Collect market info
    results = []

    for idx, row in df_sub.iterrows():
        ipo_no = row['ipo_no']
        code = row['code']
        company_name = row['company_name']

        print(f"[{idx+1}/{len(df_sub)}] {company_name} (ipo_no={ipo_no})...", end=' ')

        market = get_market_classification(ipo_no)

        if market:
            print(f"✓ {market}")
        else:
            print("✗ Not found")

        results.append({
            'ipo_no': ipo_no,
            'code': code,
            'company_name': company_name,
            'listing_method': market
        })

        # Rate limit
        time.sleep(0.5)

    # Create DataFrame
    df_market = pd.DataFrame(results)

    # Summary
    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total IPOs: {len(df_market)}")
    print(f"\nMarket distribution:")
    print(df_market['listing_method'].value_counts())
    print()

    # Save
    output_file = 'data/raw/38_market_classification.csv'
    df_market.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✅ Saved to: {output_file}")
    print()

    # Show sample
    print("Sample data:")
    print(df_market[df_market['listing_method'] == 'KOSPI'].head(10))


if __name__ == '__main__':
    main()
