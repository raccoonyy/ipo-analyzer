"""
Generate predictions for frontend using expanded 2018-2025 dataset
Creates ipo_precomputed.json with predictions for all historical IPOs
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).parent))

from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor


def main():
    """Generate predictions for frontend"""
    print("=" * 80)
    print("GENERATING FRONTEND PREDICTIONS (2018-2025)")
    print("=" * 80)
    print()

    # 1. Load expanded dataset
    print("Loading dataset...")
    input_file = "data/raw/ipo_full_dataset_2018_2025.csv"
    df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(df)} IPO records")
    print()

    # Filter to only rows with necessary data for prediction
    required_cols = [
        "code",
        "company_name",
        "listing_date",
        "ipo_price",
        "shares_offered",
        "institutional_demand_rate",
        "subscription_competition_rate",
        "lockup_ratio",
    ]

    # Check which columns exist
    df_filtered = df.dropna(
        subset=[col for col in required_cols if col in df.columns]
    ).reset_index(drop=True)
    print(f"After filtering for complete data: {len(df_filtered)} records")
    print()

    # 2. Load trained models and transformers
    print("Loading trained models and transformers...")
    predictor = IPOPricePredictor(model_type="random_forest")
    predictor.load_models("models")

    engineer = IPOFeatureEngineer()
    engineer.load_transformers("data/processed")
    print("✅ Loaded models and transformers")
    print()

    # 3. Prepare features
    print("Engineering features...")

    # Rename columns to match expected names
    df_renamed = df_filtered.copy()
    if "ipo_price" in df_renamed.columns:
        df_renamed["ipo_price_confirmed"] = df_renamed["ipo_price"]

    # Add missing columns with default values if needed
    if "industry" not in df_renamed.columns:
        df_renamed["industry"] = "Unknown"
    if "theme" not in df_renamed.columns:
        df_renamed["theme"] = "Unknown"

    features_df = engineer.engineer_features(df_renamed, fit=False)
    X = features_df[engineer.feature_names].values
    print(f"✅ Feature matrix: {X.shape}")
    print()

    # 4. Generate predictions
    print("Generating predictions...")
    predictions = predictor.predict(X)
    print("✅ Generated predictions for all targets")
    print()

    # 5. Create output JSON
    print("Creating output JSON...")

    predictions_list = []
    for idx, row in df_filtered.iterrows():
        pred_dict = {
            "code": str(row["code"]),
            "company_name": row["company_name"],
            "listing_date": row["listing_date"],
            "ipo_price": int(row["ipo_price"]) if pd.notna(row["ipo_price"]) else None,
            "predicted": {
                "day0_high": int(round(predictions["day0_high"][idx])),
                "day0_close": int(round(predictions["day0_close"][idx])),
                "day1_close": int(round(predictions["day1_close"][idx])),
            },
            "metadata": {
                "shares_offered": (
                    int(row["shares_offered"])
                    if pd.notna(row["shares_offered"])
                    else None
                ),
                "institutional_demand_rate": (
                    float(row["institutional_demand_rate"])
                    if pd.notna(row["institutional_demand_rate"])
                    else None
                ),
                "subscription_competition_rate": (
                    float(row["subscription_competition_rate"])
                    if pd.notna(row["subscription_competition_rate"])
                    else None
                ),
                "lockup_ratio": (
                    float(row["lockup_ratio"])
                    if pd.notna(row["lockup_ratio"])
                    else None
                ),
            },
        }

        # Add actual values if available (check each value individually)
        if (
            "day0_high" in row
            and pd.notna(row.get("day0_high"))
            and "day0_close" in row
            and pd.notna(row.get("day0_close"))
            and "day1_close" in row
            and pd.notna(row.get("day1_close"))
        ):
            pred_dict["actual"] = {
                "day0_high": int(row["day0_high"]),
                "day0_close": int(row["day0_close"]),
                "day1_close": int(row["day1_close"]),
            }

        predictions_list.append(pred_dict)

    # Create output structure
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_version": "v2.1",
            "total_ipos": len(predictions_list),
            "date_range": {
                "start": df_filtered["listing_date"].min(),
                "end": df_filtered["listing_date"].max(),
            },
            "features_used": engineer.feature_names,
        },
        "predictions": predictions_list,
    }

    # 6. Save to frontend public directory
    output_path = Path("../frontend/public/ipo_precomputed.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(predictions_list)} predictions to {output_path}")
    print()

    # 7. Show statistics
    print("=" * 80)
    print("PREDICTION STATISTICS")
    print("=" * 80)
    print(f"Total IPOs: {len(predictions_list)}")
    print(
        f"Date range: {output['metadata']['date_range']['start']} to {output['metadata']['date_range']['end']}"
    )
    print()

    # Calculate prediction ranges
    day0_highs = [p["predicted"]["day0_high"] for p in predictions_list]
    day0_closes = [p["predicted"]["day0_close"] for p in predictions_list]
    day1_closes = [p["predicted"]["day1_close"] for p in predictions_list]

    print("Predicted Day 0 High:")
    print(f"  Mean: ₩{np.mean(day0_highs):,.0f}")
    print(f"  Median: ₩{np.median(day0_highs):,.0f}")
    print(f"  Range: ₩{np.min(day0_highs):,.0f} - ₩{np.max(day0_highs):,.0f}")
    print()

    print("Predicted Day 1 Close:")
    print(f"  Mean: ₩{np.mean(day1_closes):,.0f}")
    print(f"  Median: ₩{np.median(day1_closes):,.0f}")
    print(f"  Range: ₩{np.min(day1_closes):,.0f} - ₩{np.max(day1_closes):,.0f}")
    print()

    # Show distribution by year
    years = {}
    for pred in predictions_list:
        year = pred["listing_date"][:4]
        years[year] = years.get(year, 0) + 1

    print("Distribution by year:")
    for year in sorted(years.keys()):
        print(f"  {year}: {years[year]} IPOs")
    print()

    # Show counts with actual data
    with_actual = sum(1 for p in predictions_list if "actual" in p)
    print(f"IPOs with actual price data: {with_actual}/{len(predictions_list)}")
    print()

    print("=" * 80)
    print("FRONTEND PREDICTIONS GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
