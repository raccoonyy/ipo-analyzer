"""
Merge 38.co.kr financial metrics into enhanced dataset
"""
import pandas as pd
import numpy as np

def merge_financial_metrics():
    """Merge 38.co.kr financial data with enhanced dataset"""

    print("=" * 80)
    print("MERGING 38.CO.KR FINANCIAL METRICS")
    print("=" * 80)
    print()

    # Load datasets
    print("Loading enhanced dataset...")
    df_main = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")
    print(f"✓ Loaded {len(df_main)} IPO records")

    print("Loading 38.co.kr financial metrics...")
    df_financial = pd.read_csv("data/raw/38_financial_metrics.csv")
    print(f"✓ Loaded {len(df_financial)} financial records")
    print()

    # Ensure code is string with 6 digits
    df_main["code"] = df_main["code"].astype(str).str.zfill(6)
    df_financial["code"] = df_financial["code"].astype(str).str.zfill(6)

    # Merge on code
    print("Merging datasets on stock code...")
    df_merged = df_main.merge(
        df_financial[["code", "per", "pbr", "eps", "roe"]],
        on="code",
        how="left"
    )

    # Rename to avoid confusion with existing day0_per, day0_pbr, day0_eps (which are all 0)
    df_merged = df_merged.rename(columns={
        "per": "listing_per",
        "pbr": "listing_pbr",
        "eps": "listing_eps",
        "roe": "listing_roe",
    })

    # Replace existing zero-value financial columns
    if "day0_per" in df_merged.columns:
        df_merged = df_merged.drop(columns=["day0_per", "day0_pbr", "day0_eps", "day0_market_cap"])

    print(f"✓ Merged successfully")
    print()

    # Statistics
    total = len(df_merged)
    with_per = df_merged["listing_per"].notna().sum()
    with_pbr = df_merged["listing_pbr"].notna().sum()
    with_eps = df_merged["listing_eps"].notna().sum()
    with_roe = df_merged["listing_roe"].notna().sum()

    print("FINANCIAL DATA COVERAGE:")
    print(f"  PER: {with_per}/{total} ({with_per/total*100:.1f}%)")
    print(f"  PBR: {with_pbr}/{total} ({with_pbr/total*100:.1f}%)")
    print(f"  EPS: {with_eps}/{total} ({with_eps/total*100:.1f}%)")
    print(f"  ROE: {with_roe}/{total} ({with_roe/total*100:.1f}%)")
    print()

    # Save
    output_file = "data/raw/ipo_full_dataset_2022_2024_with_financials.csv"
    df_merged.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ Saved merged dataset: {output_file}")
    print(f"   Total columns: {len(df_merged.columns)}")
    print()

    return df_merged


if __name__ == "__main__":
    merge_financial_metrics()
