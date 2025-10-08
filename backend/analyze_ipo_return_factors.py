"""
Analyze key factors affecting IPO returns
Identify the top 3 factors that drive successful IPO participation
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
import json


def calculate_returns(df):
    """Calculate various return metrics"""
    # Day 0 returns (IPO day)
    df["day0_high_return"] = (
        (df["day0_high"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
    )
    df["day0_close_return"] = (
        (df["day0_close"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
    )

    # Day 1 returns (next trading day, relative to day0 close)
    df["day1_close_return"] = (
        (df["day1_close"] - df["day0_close"]) / df["day0_close"] * 100
    )

    # Total return from IPO to day 1
    df["total_return_day1"] = (
        (df["day1_close"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
    )

    return df


def analyze_feature_correlations(df, return_col="day0_close_return"):
    """Analyze correlations between features and returns"""
    features = [
        "ipo_price_confirmed",
        "institutional_demand_rate",
        "subscription_competition_rate",
        "lockup_ratio",
        "ipo_price_range_pct",
    ]

    correlations = []

    for feature in features:
        if feature not in df.columns or df[feature].isna().all():
            continue

        # Filter rows with valid data
        valid_mask = df[feature].notna() & df[return_col].notna()
        if valid_mask.sum() < 10:
            continue

        # Calculate correlation
        try:
            corr, pval = spearmanr(
                df.loc[valid_mask, feature], df.loc[valid_mask, return_col]
            )
            correlations.append(
                {
                    "feature": feature,
                    "correlation": corr,
                    "p_value": pval,
                    "sample_size": valid_mask.sum(),
                }
            )
        except:
            pass

    return sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True)


def analyze_categorical_features(df, return_col="day0_close_return"):
    """Analyze how categorical features affect returns"""
    results = {}

    # Industry analysis
    if "industry" in df.columns:
        industry_returns = (
            df.groupby("industry")[return_col]
            .agg(["mean", "median", "count"])
            .sort_values("mean", ascending=False)
        )
        results["industry"] = industry_returns.to_dict("index")

    # Theme analysis
    if "theme" in df.columns:
        theme_returns = (
            df.groupby("theme")[return_col]
            .agg(["mean", "median", "count"])
            .sort_values("mean", ascending=False)
        )
        results["theme"] = theme_returns.to_dict("index")

    # Listing method analysis
    if "listing_method" in df.columns:
        method_returns = (
            df.groupby("listing_method")[return_col]
            .agg(["mean", "median", "count"])
            .sort_values("mean", ascending=False)
        )
        results["listing_method"] = method_returns.to_dict("index")

    return results


def analyze_demand_impact(df):
    """Analyze how demand metrics affect returns"""
    results = {}

    # Institutional demand categories
    df["inst_demand_category"] = pd.cut(
        df["institutional_demand_rate"],
        bins=[0, 200, 500, 1000, float("inf")],
        labels=[
            "Low (<200:1)",
            "Medium (200-500:1)",
            "High (500-1000:1)",
            "Very High (>1000:1)",
        ],
    )

    demand_analysis = (
        df.groupby("inst_demand_category", observed=True)
        .agg(
            {
                "day0_close_return": ["mean", "median", "count"],
                "day0_high_return": ["mean", "median"],
                "total_return_day1": ["mean", "median"],
            }
        )
        .round(2)
    )

    results["institutional_demand"] = demand_analysis.to_dict()

    # Subscription competition categories
    df["sub_comp_category"] = pd.cut(
        df["subscription_competition_rate"],
        bins=[0, 500, 1000, 2000, float("inf")],
        labels=[
            "Low (<500:1)",
            "Medium (500-1000:1)",
            "High (1000-2000:1)",
            "Very High (>2000:1)",
        ],
    )

    sub_analysis = (
        df.groupby("sub_comp_category", observed=True)
        .agg(
            {
                "day0_close_return": ["mean", "median", "count"],
                "day0_high_return": ["mean", "median"],
                "total_return_day1": ["mean", "median"],
            }
        )
        .round(2)
    )

    results["subscription_competition"] = sub_analysis.to_dict()

    # Lockup ratio categories
    df["lockup_category"] = pd.cut(
        df["lockup_ratio"],
        bins=[0, 30, 60, 80, 100],
        labels=["Low (<30%)", "Medium (30-60%)", "High (60-80%)", "Very High (>80%)"],
    )

    lockup_analysis = (
        df.groupby("lockup_category", observed=True)
        .agg(
            {
                "day0_close_return": ["mean", "median", "count"],
                "day0_high_return": ["mean", "median"],
                "total_return_day1": ["mean", "median"],
            }
        )
        .round(2)
    )

    results["lockup_ratio"] = lockup_analysis.to_dict()

    return results


def main():
    print("=" * 80)
    print("IPO RETURN FACTORS ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    df = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")

    # Filter out SPAC companies
    df = df[~df["company_name"].str.contains("기업인수목적", na=False)]

    # Filter for records with actual return data
    df = df[df["day0_close"].notna()]

    print(f"Analyzing {len(df)} IPOs with complete data")
    print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")
    print()

    # Calculate returns
    df = calculate_returns(df)

    # Add price range percentage
    df["ipo_price_range_pct"] = (
        (df["ipo_price_upper"] - df["ipo_price_lower"]) / df["ipo_price_lower"] * 100
    )

    print("=" * 80)
    print("1. CORRELATION ANALYSIS")
    print("=" * 80)
    print()

    for return_type in ["day0_close_return", "day0_high_return", "total_return_day1"]:
        print(f"\n{return_type.replace('_', ' ').title()}")
        print("-" * 80)
        correlations = analyze_feature_correlations(df, return_type)
        for c in correlations[:5]:
            print(
                f"  {c['feature']:35}: {c['correlation']:+.4f} (p={c['p_value']:.4f}, n={c['sample_size']})"
            )

    print()
    print("=" * 80)
    print("2. DEMAND METRICS IMPACT")
    print("=" * 80)
    print()

    demand_results = analyze_demand_impact(df)

    print("\nInstitutional Demand Rate Impact:")
    print("-" * 80)
    for category in [
        "Low (<200:1)",
        "Medium (200-500:1)",
        "High (500-1000:1)",
        "Very High (>1000:1)",
    ]:
        mask = df["inst_demand_category"] == category
        if mask.sum() > 0:
            mean_return = df.loc[mask, "day0_close_return"].mean()
            count = mask.sum()
            print(f"  {category:25}: {mean_return:+7.2f}% (n={count})")

    print("\nSubscription Competition Rate Impact:")
    print("-" * 80)
    for category in [
        "Low (<500:1)",
        "Medium (500-1000:1)",
        "High (1000-2000:1)",
        "Very High (>2000:1)",
    ]:
        mask = df["sub_comp_category"] == category
        if mask.sum() > 0:
            mean_return = df.loc[mask, "day0_close_return"].mean()
            count = mask.sum()
            print(f"  {category:25}: {mean_return:+7.2f}% (n={count})")

    print("\nLockup Ratio Impact:")
    print("-" * 80)
    for category in [
        "Low (<30%)",
        "Medium (30-60%)",
        "High (60-80%)",
        "Very High (>80%)",
    ]:
        mask = df["lockup_category"] == category
        if mask.sum() > 0:
            mean_return = df.loc[mask, "day0_close_return"].mean()
            count = mask.sum()
            print(f"  {category:25}: {mean_return:+7.2f}% (n={count})")

    print()
    print("=" * 80)
    print("3. RETURN STATISTICS")
    print("=" * 80)
    print()

    print("Day 0 Close Return Statistics:")
    print("-" * 80)
    print(f"  Mean:    {df['day0_close_return'].mean():+7.2f}%")
    print(f"  Median:  {df['day0_close_return'].median():+7.2f}%")
    print(f"  Std Dev: {df['day0_close_return'].std():7.2f}%")
    print(f"  Min:     {df['day0_close_return'].min():+7.2f}%")
    print(f"  Max:     {df['day0_close_return'].max():+7.2f}%")
    print()

    print("Success Rate (Positive Returns):")
    print("-" * 80)
    success_rate = (df["day0_close_return"] > 0).mean() * 100
    print(f"  Day 0 Close: {success_rate:.1f}%")

    # Save detailed results
    results = {
        "correlations": {
            "day0_close": analyze_feature_correlations(df, "day0_close_return"),
            "day0_high": analyze_feature_correlations(df, "day0_high_return"),
            "total_day1": analyze_feature_correlations(df, "total_return_day1"),
        },
        "demand_impact": demand_results,
        "statistics": {
            "mean_return": float(df["day0_close_return"].mean()),
            "median_return": float(df["day0_close_return"].median()),
            "success_rate": float(success_rate),
            "sample_size": len(df),
        },
    }

    with open("reports/ipo_return_factors_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print()
    print(f"✅ Saved detailed analysis to: reports/ipo_return_factors_analysis.json")
    print()


if __name__ == "__main__":
    main()
