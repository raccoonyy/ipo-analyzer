"""
Analyze IPO returns by sector (업종)
Uses sector data from 38.co.kr
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt


def calculate_returns(df):
    """Calculate return metrics"""
    df["day0_return"] = (
        (df["day0_close"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
    )
    return df


def analyze_by_sector(df):
    """Analyze returns grouped by sector"""
    # Group by sector
    sector_stats = (
        df.groupby("sector_38")
        .agg(
            {
                "day0_return": ["count", "mean", "median", "std"],
                "ipo_price_confirmed": "mean",
                "subscription_competition_rate": "mean",
                "institutional_demand_rate": "mean",
            }
        )
        .round(2)
    )

    # Flatten column names
    sector_stats.columns = [
        "_".join(col).strip() for col in sector_stats.columns.values
    ]
    sector_stats = sector_stats.rename(
        columns={
            "day0_return_count": "count",
            "day0_return_mean": "mean_return",
            "day0_return_median": "median_return",
            "day0_return_std": "std_return",
            "ipo_price_confirmed_mean": "avg_ipo_price",
            "subscription_competition_rate_mean": "avg_subscription_rate",
            "institutional_demand_rate_mean": "avg_institutional_rate",
        }
    )

    # Sort by mean return
    sector_stats = sector_stats.sort_values("mean_return", ascending=False)

    return sector_stats


def main():
    print("=" * 80)
    print("IPO RETURNS ANALYSIS BY SECTOR (업종)")
    print("=" * 80)
    print()

    # Load full dataset
    df = pd.read_csv("data/raw/ipo_full_dataset_2022_2025.csv")

    # Load sector data from 38.co.kr
    sector_data = pd.read_csv("data/raw/38_subscription_data.csv")

    print(f"Full dataset: {len(df)} IPOs")
    print(f"Sector data: {len(sector_data)} IPOs")
    print()

    # Merge sector data
    df["code"] = df["code"].astype(str).str.zfill(6)
    sector_data["code"] = sector_data["code"].astype(str).str.zfill(6)

    df = df.merge(
        sector_data[["code", "sector_38"]],
        on="code",
        how="left",
    )

    # Filter: only IPOs with sector data and actual returns
    df = df[df["sector_38"].notna() & df["day0_close"].notna()]

    # Filter out SPAC companies
    df = df[~df["company_name"].str.contains("기업인수목적", na=False)]

    print(f"IPOs with sector data and returns: {len(df)}")
    print()

    # Calculate returns
    df = calculate_returns(df)

    # Overall statistics
    print("=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"Total IPOs with sector data: {len(df)}")
    print(f"Unique sectors: {df['sector_38'].nunique()}")
    print(f"Mean return: {df['day0_return'].mean():.2f}%")
    print(f"Median return: {df['day0_return'].median():.2f}%")
    print()

    # Sector analysis
    print("=" * 80)
    print("SECTOR ANALYSIS (Top 20 by Mean Return)")
    print("=" * 80)
    print()

    sector_stats = analyze_by_sector(df)

    # Show top 20 sectors
    print(sector_stats.head(20).to_string())
    print()

    # Show bottom 10 sectors
    print("=" * 80)
    print("BOTTOM 10 SECTORS BY MEAN RETURN")
    print("=" * 80)
    print()
    print(sector_stats.tail(10).to_string())
    print()

    # Sectors with most IPOs
    print("=" * 80)
    print("SECTORS WITH MOST IPOs (Min 5 IPOs)")
    print("=" * 80)
    print()

    large_sectors = sector_stats[sector_stats["count"] >= 5].copy()
    large_sectors = large_sectors.sort_values("count", ascending=False)
    print(large_sectors.to_string())
    print()

    # Save results
    sector_stats.to_csv("reports/sector_returns_analysis.csv", encoding="utf-8-sig")
    print(f"✅ Saved detailed results to: reports/sector_returns_analysis.csv")
    print()

    # Specific sector examples
    print("=" * 80)
    print("EXAMPLE SECTORS")
    print("=" * 80)
    print()

    example_sectors = [
        "완제 의약품 제조업",
        "기타 광학기기 제조업",
        "기타 운송관련 서비스업",
        "반도체 제조업",
        "소프트웨어 개발 및 공급업",
    ]

    for sector in example_sectors:
        if sector in sector_stats.index:
            stats = sector_stats.loc[sector]
            print(f"\n{sector}:")
            print(f"  IPOs: {int(stats['count'])}")
            print(f"  Mean return: {stats['mean_return']:.2f}%")
            print(f"  Median return: {stats['median_return']:.2f}%")
            print(f"  Avg subscription rate: {stats['avg_subscription_rate']:.2f}:1")

    print()


if __name__ == "__main__":
    main()
