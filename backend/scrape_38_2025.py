"""
Scrape current IPO data from 38.co.kr including price bands
"""

import subprocess
from bs4 import BeautifulSoup
import pandas as pd
import re


def parse_price(price_str):
    """Parse price string to extract lower and upper bounds"""
    if not price_str or price_str == "-":
        return None, None

    # Remove commas and spaces
    price_str = price_str.replace(",", "").replace(" ", "")

    # Check if it's a range (e.g., "45000~58000")
    if "~" in price_str:
        parts = price_str.split("~")
        lower = int(parts[0])
        upper = int(parts[1])
        return lower, upper
    else:
        # Single price
        price = int(price_str)
        return price, price


def parse_rate(rate_str):
    """Parse rate string (e.g., '488.95:1' or '62.08%')"""
    if not rate_str or rate_str == "-":
        return 0.0

    rate_str = rate_str.replace(",", "").strip()

    # Remove :1 suffix
    if ":1" in rate_str:
        rate_str = rate_str.replace(":1", "")

    # Remove % suffix
    if "%" in rate_str:
        rate_str = rate_str.replace("%", "")

    try:
        return float(rate_str)
    except ValueError:
        return 0.0


def scrape_38_data():
    """Scrape IPO data from 38.co.kr"""
    url = "https://www.38.co.kr/html/fund/index.htm?o=r1"

    print("Fetching data from 38.co.kr...")

    # Use curl to bypass SSL issues
    result = subprocess.run(["curl", "-k", "-s", url], capture_output=True)

    # Decode with EUC-KR encoding
    html = result.stdout.decode("euc-kr", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")

    # Find the IPO table
    table = soup.find("table", {"class": "tbl_style01"})
    if not table:
        print("❌ Could not find IPO table")
        return pd.DataFrame()

    rows = table.find_all("tr")[1:]  # Skip header

    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        # Extract company name and code
        company_cell = cols[0]
        company_link = company_cell.find("a")
        if not company_link:
            continue

        company_name = company_link.text.strip()

        # Extract code from onclick or href
        onclick = company_link.get("onclick", "")
        code_match = re.search(r"code=(\d+)", onclick)
        if code_match:
            code = code_match.group(1)
        else:
            code = None

        # Extract other fields
        listing_date = cols[1].text.strip()
        price_range = cols[2].text.strip()  # 공모희망가
        final_price = cols[3].text.strip()  # 확정공모가
        institutional_rate = cols[4].text.strip()  # 기관경쟁률
        subscription_rate = cols[5].text.strip()  # 청약경쟁률
        lockup = cols[6].text.strip()  # 의무보유확약

        # Parse prices
        price_lower, price_upper = parse_price(price_range)
        final_price_val = parse_price(final_price)[0]  # Get single value

        # Parse rates
        institutional_demand_rate = parse_rate(institutional_rate)
        subscription_competition_rate = parse_rate(subscription_rate)
        lockup_ratio = parse_rate(lockup)

        data.append(
            {
                "company_name": company_name,
                "code": code,
                "listing_date": listing_date,
                "ipo_price_lower": price_lower,
                "ipo_price_upper": price_upper,
                "ipo_price_confirmed": final_price_val,
                "institutional_demand_rate": institutional_demand_rate,
                "subscription_competition_rate": subscription_competition_rate,
                "lockup_ratio": lockup_ratio,
            }
        )

    df = pd.DataFrame(data)

    # Convert listing_date to standard format
    df["listing_date"] = pd.to_datetime(
        df["listing_date"], format="%Y.%m.%d", errors="coerce"
    )

    # Filter for 2025 IPOs
    df = df[df["listing_date"].dt.year == 2025].copy()

    # Format code as 6-digit string
    df["code"] = df["code"].astype(str).str.zfill(6)

    return df


def main():
    print("=" * 80)
    print("SCRAPING 38.CO.KR IPO DATA")
    print("=" * 80)
    print()

    df = scrape_38_data()

    print(f"✓ Scraped {len(df)} IPOs from 2025")
    print()

    # Filter out SPAC companies
    if len(df) > 0:
        initial_count = len(df)
        df = df[~df["company_name"].str.contains("기업인수목적", na=False)]
        spac_count = initial_count - len(df)
        if spac_count > 0:
            print(f"Filtered out {spac_count} SPAC companies")
            print(f"Remaining IPOs: {len(df)}")
            print()

    # Save to CSV
    output_file = "data/raw/38_2025_ipo_data.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"✅ Saved to: {output_file}")
    print()

    # Show sample
    print("Sample data:")
    print(
        df[
            [
                "company_name",
                "code",
                "ipo_price_lower",
                "ipo_price_upper",
                "ipo_price_confirmed",
                "institutional_demand_rate",
            ]
        ].head(10)
    )
    print()

    # Show statistics
    print(f"IPOs with price bands: {df['ipo_price_lower'].notna().sum()}")
    print(f"IPOs with subscription data: {df['institutional_demand_rate'].gt(0).sum()}")


if __name__ == "__main__":
    main()
