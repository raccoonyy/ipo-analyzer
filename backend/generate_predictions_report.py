"""
Generate Predictions Comparison Report
Compare actual vs predicted values for trained IPO dataset
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor


def main():
    """Generate predictions comparison CSV"""
    print("=" * 80)
    print("GENERATING PREDICTIONS COMPARISON REPORT")
    print("=" * 80)
    print()

    # 1. Load dataset
    print("Loading dataset...")
    input_file = "data/raw/ipo_full_dataset_2022_2024_enhanced.csv"
    df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(df)} IPO records")
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
    features_df = engineer.engineer_features(df, fit=False)
    X = features_df[engineer.feature_names].values
    print(f"✅ Feature matrix: {X.shape}")
    print()

    # 4. Generate predictions
    print("Generating predictions...")
    predictions = predictor.predict(X)
    print("✅ Generated predictions for all targets")
    print()

    # 5. Create comparison DataFrame
    print("Creating comparison DataFrame...")
    comparison = pd.DataFrame({
        "company_name": df["company_name"],
        "code": df["code"],
        "listing_date": df["listing_date"],
        "ipo_price_confirmed": df["ipo_price_confirmed"],
        # Actual values
        "actual_day0_high": df["day0_high"],
        "actual_day0_close": df["day0_close"],
        "actual_day1_close": df["day1_close"],
        # Predicted values
        "predicted_day0_high": predictions["day0_high"],
        "predicted_day0_close": predictions["day0_close"],
        "predicted_day1_close": predictions["day1_close"],
    })

    # Calculate errors
    comparison["error_day0_high"] = comparison["predicted_day0_high"] - comparison["actual_day0_high"]
    comparison["error_day0_close"] = comparison["predicted_day0_close"] - comparison["actual_day0_close"]
    comparison["error_day1_close"] = comparison["predicted_day1_close"] - comparison["actual_day1_close"]

    # Calculate percentage errors
    comparison["error_pct_day0_high"] = (
        comparison["error_day0_high"] / comparison["actual_day0_high"] * 100
    )
    comparison["error_pct_day0_close"] = (
        comparison["error_day0_close"] / comparison["actual_day0_close"] * 100
    )
    comparison["error_pct_day1_close"] = (
        comparison["error_day1_close"] / comparison["actual_day1_close"] * 100
    )

    # Calculate absolute errors
    comparison["abs_error_day0_high"] = comparison["error_day0_high"].abs()
    comparison["abs_error_day0_close"] = comparison["error_day0_close"].abs()
    comparison["abs_error_day1_close"] = comparison["error_day1_close"].abs()

    print(f"✅ Created comparison with {len(comparison)} records")
    print()

    # 6. Save to CSV
    output_file = "reports/predictions_comparison.csv"
    comparison.to_csv(output_file, index=False, encoding="utf-8-sig")
    print("=" * 80)
    print("SAVED PREDICTIONS COMPARISON")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Records: {len(comparison)}")
    print()

    # 7. Show statistics
    print("=" * 80)
    print("PREDICTION ERROR STATISTICS")
    print("=" * 80)
    print()

    for target in ["day0_high", "day0_close", "day1_close"]:
        print(f"Target: {target}")
        print("-" * 80)

        mae = comparison[f"abs_error_{target}"].mean()
        rmse = np.sqrt((comparison[f"error_{target}"] ** 2).mean())
        mape = comparison[f"error_pct_{target}"].abs().mean()

        print(f"  Mean Absolute Error (MAE):  {mae:>10,.2f} KRW")
        print(f"  Root Mean Squared Error:    {rmse:>10,.2f} KRW")
        print(f"  Mean Abs Percentage Error:  {mape:>10.2f}%")
        print()

    # 8. Show best/worst predictions
    print("=" * 80)
    print("BEST PREDICTIONS (Lowest Absolute Error)")
    print("=" * 80)
    print()

    best_predictions = comparison.nsmallest(5, "abs_error_day0_close")[
        ["company_name", "listing_date", "actual_day0_close",
         "predicted_day0_close", "error_day0_close"]
    ]
    print(best_predictions.to_string(index=False))
    print()

    print("=" * 80)
    print("WORST PREDICTIONS (Highest Absolute Error)")
    print("=" * 80)
    print()

    worst_predictions = comparison.nlargest(5, "abs_error_day0_close")[
        ["company_name", "listing_date", "actual_day0_close",
         "predicted_day0_close", "error_day0_close"]
    ]
    print(worst_predictions.to_string(index=False))
    print()

    print("=" * 80)
    print("REPORT GENERATION COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
