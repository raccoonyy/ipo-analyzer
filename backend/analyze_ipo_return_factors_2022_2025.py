"""
Analyze key factors affecting IPO returns - Full dataset (2022-2025)
Compare results with 2022-2024 analysis
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import json


def calculate_returns(df):
    """Calculate various return metrics"""
    # Day 0 returns (IPO day)
    df["day0_high_return"] = (
        (df["day0_high"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
    )
    df["day0_close_return"] = (
        (df["day0_close"] - df["ipo_price_confirmed"])
        / df["ipo_price_confirmed"]
        * 100
    )

    # Day 1 returns (next trading day, relative to day0 close)
    df["day1_close_return"] = (
        (df["day1_close"] - df["day0_close"]) / df["day0_close"] * 100
    )

    # Total return from IPO to day 1
    df["total_return_day1"] = (
        (df["day1_close"] - df["ipo_price_confirmed"])
        / df["ipo_price_confirmed"]
        * 100
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

    # Lockup ratio categories
    df["lockup_category"] = pd.cut(
        df["lockup_ratio"],
        bins=[0, 30, 60, 80, 100],
        labels=["Low (<30%)", "Medium (30-60%)", "High (60-80%)", "Very High (>80%)"],
    )

    return results


def compare_datasets():
    """Compare 2022-2024 vs 2022-2025 analysis"""

    print("=" * 80)
    print("IPO RETURN FACTORS ANALYSIS COMPARISON")
    print("=" * 80)
    print()

    results = {}

    # Analyze both datasets
    for dataset_name, file_path in [
        ("2022-2024", "data/raw/ipo_full_dataset_2022_2024_enhanced.csv"),
        ("2022-2025", "data/raw/ipo_full_dataset_2022_2025.csv"),
    ]:
        print(f"\n{'=' * 80}")
        print(f"ANALYZING: {dataset_name}")
        print("=" * 80)
        print()

        # Load data
        df = pd.read_csv(file_path)

        # Filter out SPAC companies
        df = df[~df["company_name"].str.contains("기업인수목적", na=False)]

        # Filter for records with actual return data
        df = df[df["day0_close"].notna()]

        print(f"Sample size: {len(df)} IPOs")
        print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")
        print()

        # Calculate returns
        df = calculate_returns(df)

        # Add price range percentage
        df["ipo_price_range_pct"] = (
            (df["ipo_price_upper"] - df["ipo_price_lower"])
            / df["ipo_price_lower"]
            * 100
        )

        # Correlation Analysis
        print("CORRELATION ANALYSIS (Day 0 Close Return)")
        print("-" * 80)
        correlations = analyze_feature_correlations(df, "day0_close_return")
        for c in correlations[:5]:
            print(
                f"  {c['feature']:35}: {c['correlation']:+.4f} (p={c['p_value']:.4f}, n={c['sample_size']})"
            )

        # Demand Impact Analysis
        print()
        print("DEMAND METRICS IMPACT")
        print("-" * 80)

        analyze_demand_impact(df)

        # Subscription Competition Rate
        print("\nSubscription Competition Rate Impact:")
        for category in [
            "Low (<500:1)",
            "Medium (500-1000:1)",
            "High (1000-2000:1)",
            "Very High (>2000:1)",
        ]:
            mask = df["sub_comp_category"] == category
            if mask.sum() > 0:
                mean_return = df.loc[mask, "day0_close_return"].mean()
                median_return = df.loc[mask, "day0_close_return"].median()
                count = mask.sum()
                print(
                    f"  {category:25}: Mean {mean_return:+7.2f}% | Median {median_return:+7.2f}% | n={count}"
                )

        # Institutional Demand Rate
        print("\nInstitutional Demand Rate Impact:")
        for category in [
            "Low (<200:1)",
            "Medium (200-500:1)",
            "High (500-1000:1)",
            "Very High (>1000:1)",
        ]:
            mask = df["inst_demand_category"] == category
            if mask.sum() > 0:
                mean_return = df.loc[mask, "day0_close_return"].mean()
                median_return = df.loc[mask, "day0_close_return"].median()
                count = mask.sum()
                print(
                    f"  {category:25}: Mean {mean_return:+7.2f}% | Median {median_return:+7.2f}% | n={count}"
                )

        # Lockup Ratio
        print("\nLockup Ratio Impact:")
        for category in [
            "Low (<30%)",
            "Medium (30-60%)",
            "High (60-80%)",
            "Very High (>80%)",
        ]:
            mask = df["lockup_category"] == category
            if mask.sum() > 0:
                mean_return = df.loc[mask, "day0_close_return"].mean()
                median_return = df.loc[mask, "day0_close_return"].median()
                count = mask.sum()
                print(
                    f"  {category:25}: Mean {mean_return:+7.2f}% | Median {median_return:+7.2f}% | n={count}"
                )

        # Return Statistics
        print()
        print("RETURN STATISTICS")
        print("-" * 80)
        print(f"  Mean:    {df['day0_close_return'].mean():+7.2f}%")
        print(f"  Median:  {df['day0_close_return'].median():+7.2f}%")
        print(f"  Std Dev: {df['day0_close_return'].std():7.2f}%")
        print(f"  Min:     {df['day0_close_return'].min():+7.2f}%")
        print(f"  Max:     {df['day0_close_return'].max():+7.2f}%")

        success_rate = (df["day0_close_return"] > 0).mean() * 100
        print(f"  Success Rate: {success_rate:.1f}%")

        # Store results
        results[dataset_name] = {
            "sample_size": len(df),
            "date_range": f"{df['listing_date'].min()} to {df['listing_date'].max()}",
            "correlations": correlations,
            "mean_return": float(df["day0_close_return"].mean()),
            "median_return": float(df["day0_close_return"].median()),
            "success_rate": float(success_rate),
        }

    print()
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    print()

    print("Sample Size:")
    print(f"  2022-2024: {results['2022-2024']['sample_size']} IPOs")
    print(f"  2022-2025: {results['2022-2025']['sample_size']} IPOs")
    print(
        f"  Difference: +{results['2022-2025']['sample_size'] - results['2022-2024']['sample_size']} IPOs"
    )
    print()

    print("Mean Day 0 Return:")
    print(f"  2022-2024: {results['2022-2024']['mean_return']:+.2f}%")
    print(f"  2022-2025: {results['2022-2025']['mean_return']:+.2f}%")
    print(
        f"  Difference: {results['2022-2025']['mean_return'] - results['2022-2024']['mean_return']:+.2f}%p"
    )
    print()

    print("Median Day 0 Return:")
    print(f"  2022-2024: {results['2022-2024']['median_return']:+.2f}%")
    print(f"  2022-2025: {results['2022-2025']['median_return']:+.2f}%")
    print(
        f"  Difference: {results['2022-2025']['median_return'] - results['2022-2024']['median_return']:+.2f}%p"
    )
    print()

    print("Success Rate:")
    print(f"  2022-2024: {results['2022-2024']['success_rate']:.1f}%")
    print(f"  2022-2025: {results['2022-2025']['success_rate']:.1f}%")
    print(
        f"  Difference: {results['2022-2025']['success_rate'] - results['2022-2024']['success_rate']:+.1f}%p"
    )
    print()

    print("Top 3 Correlation Changes:")
    print("-" * 80)
    for feature in [
        "subscription_competition_rate",
        "lockup_ratio",
        "institutional_demand_rate",
    ]:
        corr_2024 = next(
            (
                c["correlation"]
                for c in results["2022-2024"]["correlations"]
                if c["feature"] == feature
            ),
            None,
        )
        corr_2025 = next(
            (
                c["correlation"]
                for c in results["2022-2025"]["correlations"]
                if c["feature"] == feature
            ),
            None,
        )
        if corr_2024 is not None and corr_2025 is not None:
            print(
                f"  {feature:35}: {corr_2024:+.4f} → {corr_2025:+.4f} (Δ{corr_2025-corr_2024:+.4f})"
            )

    # Save comparison
    with open(
        "reports/ipo_return_factors_comparison_2024_vs_2025.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print()
    print(
        f"✅ Saved comparison to: reports/ipo_return_factors_comparison_2024_vs_2025.json"
    )
    print()


if __name__ == "__main__":
    compare_datasets()
