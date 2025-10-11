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


def safe_value(val):
    """Convert value to JSON-safe format (handle NaN, None, etc.)"""
    if pd.isna(val):
        return None
    return val


def safe_int(val):
    """Safely convert to int or return None"""
    if pd.isna(val):
        return None
    try:
        return int(val)
    except:
        return None


def safe_float(val):
    """Safely convert to float or return None"""
    if pd.isna(val):
        return None
    try:
        return float(val)
    except:
        return None


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
        df_renamed["industry"] = "기타"
    if "theme" not in df_renamed.columns:
        df_renamed["theme"] = "주권"

    features_df = engineer.engineer_features(df_renamed, fit=False)
    X = features_df[engineer.feature_names].values
    print(f"✅ Feature matrix: {X.shape}")
    print()

    # 4. Generate predictions
    print("Generating predictions...")
    predictions = predictor.predict(X)
    print("✅ Generated predictions for all targets")
    print()

    # 5. Create output JSON (matching frontend expected format)
    print("Creating output JSON...")

    ipos_list = []
    for idx, row in df_filtered.iterrows():
        ipo_price = safe_int(row.get("ipo_price")) or safe_int(
            row.get("ipo_price_confirmed")
        )
        pred_day0_high = int(round(predictions["day0_high"][idx]))
        pred_day0_close = int(round(predictions["day0_close"][idx]))
        pred_day1_close = int(round(predictions["day1_close"][idx]))

        ipo_dict = {
            "id": int(idx),
            "code": str(row["code"]),
            "company_name": str(row["company_name"]),
            "listing_date": str(row["listing_date"]),
            "industry": safe_value(row.get("industry", "기타")) or "기타",
            "theme": safe_value(row.get("theme", "주권")) or "주권",
            "ipo_price_lower": safe_int(row.get("ipo_price_lower")),
            "ipo_price_upper": safe_int(row.get("ipo_price_upper")),
            "ipo_price_confirmed": ipo_price,
            "shares_offered": safe_int(row.get("shares_offered")),
            "institutional_demand_rate": safe_float(
                row.get("institutional_demand_rate")
            ),
            "subscription_competition_rate": safe_float(
                row.get("subscription_competition_rate")
            ),
            "lockup_ratio": safe_float(row.get("lockup_ratio")),
            "predicted_day0_high": pred_day0_high,
            "predicted_day0_close": pred_day0_close,
            "predicted_day1_close": pred_day1_close,
        }

        # Calculate return percentages
        if ipo_price:
            ipo_dict["predicted_day0_high_return"] = round(
                (pred_day0_high - ipo_price) / ipo_price * 100, 2
            )
            ipo_dict["predicted_day0_close_return"] = round(
                (pred_day0_close - ipo_price) / ipo_price * 100, 2
            )
            ipo_dict["predicted_day1_close_return"] = round(
                (pred_day1_close - ipo_price) / ipo_price * 100, 2
            )
            ipo_dict["predicted_day0_to_day1_return"] = round(
                (pred_day1_close - pred_day0_close) / pred_day0_close * 100, 2
            )

        # Add actual values if available (check each value individually)
        if (
            "day0_high" in row
            and pd.notna(row.get("day0_high"))
            and "day0_close" in row
            and pd.notna(row.get("day0_close"))
            and "day1_close" in row
            and pd.notna(row.get("day1_close"))
        ):
            actual_day0_high = int(row["day0_high"])
            actual_day0_close = int(row["day0_close"])
            actual_day1_close = int(row["day1_close"])

            ipo_dict["actual_day0_high"] = actual_day0_high
            ipo_dict["actual_day0_close"] = actual_day0_close
            ipo_dict["actual_day1_close"] = actual_day1_close

            # Calculate actual returns
            if ipo_price:
                ipo_dict["actual_day0_high_return"] = round(
                    (actual_day0_high - ipo_price) / ipo_price * 100, 2
                )
                ipo_dict["actual_day0_close_return"] = round(
                    (actual_day0_close - ipo_price) / ipo_price * 100, 2
                )
                ipo_dict["actual_day1_close_return"] = round(
                    (actual_day1_close - ipo_price) / ipo_price * 100, 2
                )

        ipos_list.append(ipo_dict)

    # Create output structure (matching frontend expected format)
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_version": "v2.1",
            "total_ipos": len(ipos_list),
            "date_range": {
                "start": df_filtered["listing_date"].min(),
                "end": df_filtered["listing_date"].max(),
            },
            "features_used": engineer.feature_names,
            "model_type": "random_forest",
        },
        "ipos": ipos_list,
    }

    # 6. Save to frontend public directory
    output_path = Path("../frontend/public/ipo_precomputed.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(ipos_list)} IPO predictions to {output_path}")
    print()

    # 7. Show statistics
    print("=" * 80)
    print("PREDICTION STATISTICS")
    print("=" * 80)
    print(f"Total IPOs: {len(ipos_list)}")
    print(
        f"Date range: {output['metadata']['date_range']['start']} to {output['metadata']['date_range']['end']}"
    )
    print()

    # Calculate prediction ranges
    day0_highs = [p["predicted_day0_high"] for p in ipos_list]
    day0_closes = [p["predicted_day0_close"] for p in ipos_list]
    day1_closes = [p["predicted_day1_close"] for p in ipos_list]

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
    for ipo in ipos_list:
        year = ipo["listing_date"][:4]
        years[year] = years.get(year, 0) + 1

    print("Distribution by year:")
    for year in sorted(years.keys()):
        print(f"  {year}: {years[year]} IPOs")
    print()

    # Show counts with actual data
    with_actual = sum(1 for p in ipos_list if "actual_day0_high" in p)
    print(f"IPOs with actual price data: {with_actual}/{len(ipos_list)}")
    print()

    print("=" * 80)
    print("FRONTEND PREDICTIONS GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
