"""
Generate return calculator data for frontend
Calculates expected returns based on subscription competition rate and lockup ratio
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

# Load data
df = pd.read_csv("data/raw/ipo_full_dataset_2022_2025.csv")
df["day1_return"] = (
    (df["day1_close"] - df["ipo_price_confirmed"]) / df["ipo_price_confirmed"] * 100
)
df = df[df["day1_return"].notna()].copy()

print("=" * 80)
print("GENERATING RETURN CALCULATOR DATA")
print("=" * 80)
print(f"Total records: {len(df)}")
print()

# 1. Create bins for heatmap
df["comp_bin"] = pd.cut(
    df["subscription_competition_rate"],
    bins=[0, 500, 1000, 2000, float("inf")],
    labels=["Low (<500)", "Medium (500-1K)", "High (1K-2K)", "Very High (>2K)"],
)

df["lockup_bin"] = pd.cut(
    df["lockup_ratio"],
    bins=[0, 30, 60, 100],
    labels=["Low (<30%)", "Medium (30-60%)", "High (>60%)"],
)

# 2. Calculate heatmap data
heatmap_data = []

for comp_level in ["Low (<500)", "Medium (500-1K)", "High (1K-2K)", "Very High (>2K)"]:
    for lockup_level in ["Low (<30%)", "Medium (30-60%)", "High (>60%)"]:
        subset = df[
            (df["comp_bin"] == comp_level) & (df["lockup_bin"] == lockup_level)
        ]

        if len(subset) >= 3:  # At least 3 samples
            mean_return = subset["day1_return"].mean()
            median_return = subset["day1_return"].median()
            std_return = subset["day1_return"].std()
            count = len(subset)

            heatmap_data.append(
                {
                    "competition": comp_level,
                    "lockup": lockup_level,
                    "mean_return": round(mean_return, 2),
                    "median_return": round(median_return, 2),
                    "std_return": round(std_return, 2),
                    "count": int(count),
                }
            )
        else:
            # Not enough data - use adjacent bin average or overall average
            heatmap_data.append(
                {
                    "competition": comp_level,
                    "lockup": lockup_level,
                    "mean_return": None,
                    "median_return": None,
                    "std_return": None,
                    "count": 0,
                }
            )

print("Heatmap data points generated:", len(heatmap_data))
print()

# 3. Calculate price adjustment factors
price_bins = {
    "0-10K": (0, 10000),
    "10-20K": (10000, 20000),
    "20-50K": (20000, 50000),
    "50K+": (50000, float("inf")),
}

price_factors = {}
overall_mean = df["day1_return"].mean()

for label, (min_price, max_price) in price_bins.items():
    subset = df[
        (df["ipo_price_confirmed"] >= min_price)
        & (df["ipo_price_confirmed"] < max_price)
    ]

    if len(subset) >= 5:
        bin_mean = subset["day1_return"].mean()
        # Factor = bin_mean / overall_mean
        factor = bin_mean / overall_mean if overall_mean != 0 else 1.0
        price_factors[label] = {
            "factor": round(factor, 3),
            "mean_return": round(bin_mean, 2),
            "count": int(len(subset)),
        }

print("Price adjustment factors calculated:", len(price_factors))
print()

# 4. Calculate competition rate impact (detailed)
comp_detailed = []
for rate in range(0, 3100, 100):  # 0 to 3000 in steps of 100
    if rate < 500:
        base_return = df[df["subscription_competition_rate"] < 500][
            "day1_return"
        ].mean()
    elif rate < 1000:
        base_return = df[
            (df["subscription_competition_rate"] >= 500)
            & (df["subscription_competition_rate"] < 1000)
        ]["day1_return"].mean()
    elif rate < 2000:
        base_return = df[
            (df["subscription_competition_rate"] >= 1000)
            & (df["subscription_competition_rate"] < 2000)
        ]["day1_return"].mean()
    else:
        base_return = df[df["subscription_competition_rate"] >= 2000][
            "day1_return"
        ].mean()

    comp_detailed.append({"rate": rate, "expected_return": round(base_return, 2)})

# 5. Calculate lockup impact (detailed)
lockup_detailed = []
for ratio in range(0, 105, 5):  # 0 to 100 in steps of 5
    if ratio < 30:
        base_return = df[df["lockup_ratio"] < 30]["day1_return"].mean()
    elif ratio < 60:
        base_return = df[(df["lockup_ratio"] >= 30) & (df["lockup_ratio"] < 60)][
            "day1_return"
        ].mean()
    else:
        base_return = df[df["lockup_ratio"] >= 60]["day1_return"].mean()

    lockup_detailed.append({"ratio": ratio, "expected_return": round(base_return, 2)})

# 6. Top combinations
top_combinations = []
combo_stats = (
    df.groupby(["comp_bin", "lockup_bin"])["day1_return"]
    .agg(["mean", "count"])
    .reset_index()
)
combo_stats = combo_stats[combo_stats["count"] >= 3].sort_values(
    "mean", ascending=False
)

for _, row in combo_stats.head(5).iterrows():
    top_combinations.append(
        {
            "competition": str(row["comp_bin"]),
            "lockup": str(row["lockup_bin"]),
            "expected_return": round(row["mean"], 2),
            "sample_count": int(row["count"]),
        }
    )

print("Top 5 combinations identified")
print()

# 7. Compile output
output = {
    "metadata": {
        "total_samples": int(len(df)),
        "overall_mean_return": round(df["day1_return"].mean(), 2),
        "overall_median_return": round(df["day1_return"].median(), 2),
        "data_period": "2022-2025",
    },
    "heatmap_data": heatmap_data,
    "price_factors": price_factors,
    "competition_curve": comp_detailed,
    "lockup_curve": lockup_detailed,
    "top_combinations": top_combinations,
}

# 8. Save to frontend public directory
output_path = Path("../frontend/public/calculator_data.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Calculator data saved to: {output_path}")
print()

# 9. Display summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Overall mean return: {output['metadata']['overall_mean_return']:.2f}%")
print(f"Heatmap cells: {len([h for h in heatmap_data if h['count'] > 0])}/{len(heatmap_data)} with data")
print(f"Price factors: {len(price_factors)}")
print()

print("Sample heatmap values:")
for item in heatmap_data[:6]:
    if item["count"] > 0:
        print(
            f"  {item['competition']:20} + {item['lockup']:20} = {item['mean_return']:6.2f}% (n={item['count']})"
        )
print()

print("Price factors:")
for label, data in price_factors.items():
    print(
        f"  {label:10} : factor={data['factor']:.3f}, mean={data['mean_return']:6.2f}% (n={data['count']})"
    )
print()
