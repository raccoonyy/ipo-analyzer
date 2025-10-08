"""
Collect financial metrics (PER, PBR, EPS) from 38.co.kr
"""
import subprocess
import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


def extract_financial_metrics_from_fund_page(ipo_no):
    """
    Fetch financial metrics from 38.co.kr fund detail page
    Returns: dict with PER, PBR, EPS values
    """
    url = f"https://www.38.co.kr/html/fund/?o=v&no={ipo_no}&l="

    try:
        result = subprocess.run(
            ["curl", "-s", "-k", url],
            capture_output=True,
            timeout=15
        )
        html = result.stdout.decode("euc-kr", errors="ignore")

        # Check for error message
        if "해당 정보가 없습니다" in html or len(html) < 500:
            return None

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        metrics = {}

        # Extract PER (most recent year)
        per_match = re.search(r"PER[^\d]+([\d,]+\.?\d*)", text)
        if per_match:
            per_str = per_match.group(1).replace(",", "")
            try:
                metrics["per"] = float(per_str)
            except:
                metrics["per"] = 0.0

        # Extract PBR (most recent year)
        pbr_match = re.search(r"PBR[^\d]+([\d,]+\.?\d*)", text)
        if pbr_match:
            pbr_str = pbr_match.group(1).replace(",", "")
            try:
                metrics["pbr"] = float(pbr_str)
            except:
                metrics["pbr"] = 0.0

        # Extract EPS (most recent year)
        eps_match = re.search(r"EPS[^\d]+([\d,]+\.?\d*)", text)
        if eps_match:
            eps_str = eps_match.group(1).replace(",", "")
            try:
                metrics["eps"] = float(eps_str)
            except:
                metrics["eps"] = 0.0

        # Extract ROE if available
        roe_match = re.search(r"ROE[^\d]+([\d,]+\.?\d*)%?", text)
        if roe_match:
            roe_str = roe_match.group(1).replace(",", "")
            try:
                metrics["roe"] = float(roe_str)
            except:
                pass

        return metrics if metrics else None

    except Exception as e:
        print(f"  Error fetching ipo_no {ipo_no}: {e}")
        return None


def collect_financial_data_for_dataset(dataset_path, subscription_data_path):
    """
    Load IPO dataset and collect financial metrics from 38.co.kr using ipo_no mapping
    """
    print("=" * 80)
    print("COLLECTING FINANCIAL METRICS FROM 38.CO.KR")
    print("=" * 80)
    print()

    # Load datasets
    print(f"Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"✓ Loaded {len(df)} IPO records")

    print(f"Loading subscription data: {subscription_data_path}")
    df_sub = pd.read_csv(subscription_data_path)
    print(f"✓ Loaded {len(df_sub)} subscription records")
    print()

    # Create stock code → ipo_no mapping
    df_sub["code"] = df_sub["code"].astype(str).str.zfill(6)
    mapping = dict(zip(df_sub["code"], df_sub["ipo_no"]))
    print(f"✓ Created {len(mapping)} stock code → ipo_no mappings")
    print()

    # Collect financial data
    results = []
    found_count = 0
    no_mapping_count = 0
    no_data_count = 0

    for idx, row in df.iterrows():
        code = str(row["code"]).zfill(6)
        company_name = row["company_name"]
        listing_date = row.get("listing_date", "")
        listing_year = int(str(listing_date)[:4]) if listing_date else None

        # Check if we have ipo_no for this stock
        if code not in mapping:
            no_mapping_count += 1
            results.append({
                "code": code,
                "company_name": company_name,
                "listing_year": listing_year,
                "ipo_no": None,
                "per": None,
                "pbr": None,
                "eps": None,
                "roe": None,
            })
            continue

        ipo_no = mapping[code]
        print(f"[{idx+1}/{len(df)}] {company_name} ({code}, {listing_year}): Fetching ipo_no={ipo_no}...", end=" ")

        metrics = extract_financial_metrics_from_fund_page(ipo_no)

        if metrics:
            found_count += 1
            print(f"✓ PER={metrics.get('per', 'N/A')}, PBR={metrics.get('pbr', 'N/A')}, EPS={metrics.get('eps', 'N/A')}")
            results.append({
                "code": code,
                "company_name": company_name,
                "listing_year": listing_year,
                "ipo_no": ipo_no,
                "per": metrics.get("per"),
                "pbr": metrics.get("pbr"),
                "eps": metrics.get("eps"),
                "roe": metrics.get("roe"),
            })
        else:
            no_data_count += 1
            print("✗ No financial data")
            results.append({
                "code": code,
                "company_name": company_name,
                "listing_year": listing_year,
                "ipo_no": ipo_no,
                "per": None,
                "pbr": None,
                "eps": None,
                "roe": None,
            })

        # Rate limiting
        time.sleep(0.5)

    print()
    print("=" * 80)

    # Create results dataframe
    df_financial = pd.DataFrame(results)

    # Statistics
    total = len(df_financial)
    with_ipo_no = df_financial["ipo_no"].notna().sum()
    with_per = df_financial["per"].notna().sum()
    with_pbr = df_financial["pbr"].notna().sum()
    with_eps = df_financial["eps"].notna().sum()

    print(f"RESULTS:")
    print(f"  Total IPOs: {total}")
    print(f"  With ipo_no mapping: {with_ipo_no} ({with_ipo_no/total*100:.1f}%)")
    print(f"  No mapping: {no_mapping_count}")
    print(f"  With financial data: {found_count} ({found_count/total*100:.1f}%)")
    print(f"  No financial data: {no_data_count}")
    print()
    print(f"METRICS COVERAGE:")
    print(f"  PER: {with_per} ({with_per/total*100:.1f}%)")
    print(f"  PBR: {with_pbr} ({with_pbr/total*100:.1f}%)")
    print(f"  EPS: {with_eps} ({with_eps/total*100:.1f}%)")
    print()

    # Save results
    output_file = "data/raw/38_financial_metrics.csv"
    df_financial.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ Saved financial metrics to: {output_file}")

    return df_financial


if __name__ == "__main__":
    dataset_path = "data/raw/ipo_full_dataset_2022_2024_enhanced.csv"
    subscription_data_path = "data/raw/38_subscription_data.csv"
    collect_financial_data_for_dataset(dataset_path, subscription_data_path)
