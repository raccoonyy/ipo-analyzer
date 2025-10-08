"""
Backtest IPO prediction model on 2025 IPOs

This script:
1. Loads the trained model
2. Makes predictions on 2025 IPOs
3. Compares predictions with actual results
4. Generates a detailed backtesting report
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


def calculate_metrics(actual, predicted):
    """Calculate prediction metrics"""
    # Remove NaN values
    mask = ~(pd.isna(actual) | pd.isna(predicted))
    actual = actual[mask]
    predicted = predicted[mask]

    if len(actual) == 0:
        return {}

    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = np.mean(np.abs((actual - predicted) / actual)) * 100

    # R² score
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    ss_res = np.sum((actual - predicted) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # Accuracy within X%
    acc_10 = np.mean(np.abs((actual - predicted) / actual) <= 0.10) * 100
    acc_20 = np.mean(np.abs((actual - predicted) / actual) <= 0.20) * 100
    acc_30 = np.mean(np.abs((actual - predicted) / actual) <= 0.30) * 100

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "r2": r2,
        "acc_10": acc_10,
        "acc_20": acc_20,
        "acc_30": acc_30,
        "n": len(actual),
    }


def main():
    print("=" * 80)
    print("2025 IPO PREDICTION BACKTESTING")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load enhanced 2025 IPO data
    print("Loading enhanced 2025 IPO data...")
    df = pd.read_csv("data/raw/ipo_2025_dataset_enhanced.csv")
    print(f"Total 2025 IPOs: {len(df)}")
    print()

    # Filter IPOs with actual day0/day1 data
    df_day0 = df[df["day0_close"].notna()].copy()
    df_day1 = df[df["day1_close"].notna()].copy()

    print(f"IPOs with day0 data: {len(df_day0)}")
    print(f"IPOs with day1 data: {len(df_day1)}")
    print()

    # Feature engineering (same as training)
    print("Feature engineering...")
    from src.features.feature_engineering import IPOFeatureEngineer
    from src.models.ipo_predictor import IPOPricePredictor

    engineer = IPOFeatureEngineer()
    engineer.load_transformers("data/processed")
    features_df = engineer.engineer_features(df, fit=False)
    X = features_df[engineer.feature_names].values
    print(f"Feature matrix shape: {X.shape}")
    print()

    # Load trained models
    print("Loading trained models...")
    predictor = IPOPricePredictor(model_type="random_forest")
    predictor.load_models("models")
    print("✓ Models loaded")
    print()

    # Make predictions
    print("=" * 80)
    print("MAKING PREDICTIONS")
    print("=" * 80)
    print()

    predictions = predictor.predict(X)
    for target, pred in predictions.items():
        df[f"predicted_{target}"] = pred
        print(f"✓ Predicted {target}: {len(pred)} values")

    print()

    # Evaluate predictions
    print("=" * 80)
    print("EVALUATION RESULTS")
    print("=" * 80)
    print()

    results = {}

    for target in ["day0_high", "day0_close", "day1_close"]:
        actual = df[target]
        predicted = df[f"predicted_{target}"]

        metrics = calculate_metrics(actual, predicted)
        results[target] = metrics

        print(f"{target.upper()}")
        print("-" * 80)
        if metrics:
            print(f"  Sample size: {metrics['n']}")
            print(f"  MAE: {metrics['mae']:,.0f}원")
            print(f"  RMSE: {metrics['rmse']:,.0f}원")
            print(f"  MAPE: {metrics['mape']:.2f}%")
            print(f"  R²: {metrics['r2']:.4f}")
            print(f"  Accuracy within ±10%: {metrics['acc_10']:.1f}%")
            print(f"  Accuracy within ±20%: {metrics['acc_20']:.1f}%")
            print(f"  Accuracy within ±30%: {metrics['acc_30']:.1f}%")
        else:
            print("  No data available")
        print()

    # Detailed analysis: Select 5-10 IPOs for detailed comparison
    print("=" * 80)
    print("DETAILED ANALYSIS: SAMPLE IPOs")
    print("=" * 80)
    print()

    # Select representative IPOs (exclude SPACs)
    df_sample = df[~df["company_name"].str.contains("기업인수목적")].copy()

    # Select 10 IPOs with both day0 and day1 data
    df_sample = df_sample[df_sample["day0_close"].notna() & df_sample["day1_close"].notna()]

    if len(df_sample) > 10:
        # Select diverse sample: some high performers, some low performers
        df_sample = df_sample.sort_values("day0_close", ascending=False)
        sample_indices = []

        # Top 3 performers
        sample_indices.extend(df_sample.head(3).index.tolist())

        # Middle 4
        mid_start = len(df_sample) // 2 - 2
        sample_indices.extend(df_sample.iloc[mid_start : mid_start + 4].index.tolist())

        # Bottom 3
        sample_indices.extend(df_sample.tail(3).index.tolist())

        df_sample = df.loc[sample_indices]
    else:
        df_sample = df_sample.head(10)

    for idx, row in df_sample.iterrows():
        company = row["company_name"]
        code = row["code"]
        listing_date = row["listing_date"]
        ipo_price = row["ipo_price_confirmed"]

        print(f"{company} ({code}) - Listed: {listing_date}")
        print(f"  IPO Price: {ipo_price:,.0f}원")
        print()

        # Day0 predictions
        if pd.notna(row["day0_close"]):
            actual_day0 = row["day0_close"]
            pred_day0 = row["predicted_day0_close"]
            error_day0 = (pred_day0 - actual_day0) / actual_day0 * 100

            print(f"  Day0 Close:")
            print(f"    Actual:    {actual_day0:>10,.0f}원")
            print(f"    Predicted: {pred_day0:>10,.0f}원")
            print(f"    Error:     {error_day0:>10.1f}%")
            print()

        # Day1 predictions
        if pd.notna(row["day1_close"]):
            actual_day1 = row["day1_close"]
            pred_day1 = row["predicted_day1_close"]
            error_day1 = (pred_day1 - actual_day1) / actual_day1 * 100

            print(f"  Day1 Close:")
            print(f"    Actual:    {actual_day1:>10,.0f}원")
            print(f"    Predicted: {pred_day1:>10,.0f}원")
            print(f"    Error:     {error_day1:>10.1f}%")
            print()

        print()

    # Save predictions
    output_file = "reports/backtest_2025_predictions.csv"
    Path("reports").mkdir(exist_ok=True)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ Saved predictions to: {output_file}")
    print()

    # Summary
    print("=" * 80)
    print("BACKTESTING SUMMARY")
    print("=" * 80)
    print()
    print("Model Performance on 2025 IPOs:")
    print("-" * 80)

    for target in ["day0_close", "day1_close"]:
        metrics = results[target]
        if metrics:
            print(f"{target.upper()}:")
            print(f"  - Sample size: {metrics['n']}")
            print(f"  - Average error: {metrics['mape']:.1f}%")
            print(f"  - Predictions within ±20%: {metrics['acc_20']:.1f}%")
        else:
            print(f"{target.upper()}: No data")

    print()
    print("✅ Backtesting complete")


if __name__ == "__main__":
    main()
