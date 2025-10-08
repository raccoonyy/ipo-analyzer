"""
Time-based Split Backtesting
Train on 2022-2024 H1, test on 2024 H2 as "future" data
"""

import pandas as pd
import numpy as np
from datetime import datetime
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Run time-based split backtesting"""
    print("=" * 80)
    print("TIME-BASED SPLIT BACKTESTING")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Load full dataset
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    input_file = "data/raw/ipo_full_dataset_2022_2024_enhanced.csv"
    df = pd.read_csv(input_file)
    df["listing_date"] = pd.to_datetime(df["listing_date"])

    print(f"Total IPO records: {len(df)}")
    print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")
    print()

    # 2. Split by time
    print("=" * 80)
    print("TIME-BASED SPLIT")
    print("=" * 80)

    split_date = pd.to_datetime("2024-07-01")

    df_train = df[df["listing_date"] < split_date].copy()
    df_test = df[df["listing_date"] >= split_date].copy()

    print(f"Training set: {len(df_train)} IPOs ({df_train['listing_date'].min()} to {df_train['listing_date'].max()})")
    print(f"Test set: {len(df_test)} IPOs ({df_test['listing_date'].min()} to {df_test['listing_date'].max()})")
    print()

    # 3. Feature engineering
    print("=" * 80)
    print("FEATURE ENGINEERING")
    print("=" * 80)

    engineer = IPOFeatureEngineer()

    # Prepare training data
    X_train, y_train_dict, metadata_train = engineer.prepare_training_data(df_train)
    print(f"Training features: {X_train.shape}")

    # Prepare test data (fit=False)
    features_test = engineer.engineer_features(df_test, fit=False)
    X_test = features_test[engineer.feature_names].values
    print(f"Test features: {X_test.shape}")
    print()

    # 4. Train model
    print("=" * 80)
    print("TRAINING MODEL")
    print("=" * 80)
    print(f"Training on {len(df_train)} IPOs (2022-06 ~ 2024-06)")
    print()

    predictor = IPOPricePredictor(model_type="random_forest")

    # Train without splitting (use all training data)
    for target_name, y_train in y_train_dict.items():
        logger.info(f"Training model for {target_name}...")
        predictor.models[target_name].fit(X_train, y_train)

    print("✅ Training complete")
    print()

    # 5. Generate predictions on test set
    print("=" * 80)
    print("GENERATING PREDICTIONS ON TEST SET (2024 H2)")
    print("=" * 80)

    predictions = predictor.predict(X_test)

    # Actual values
    y_test_dict = {
        "day0_high": df_test["day0_high"].values,
        "day0_close": df_test["day0_close"].values,
        "day1_close": df_test["day1_close"].values,
    }

    print(f"✅ Generated predictions for {len(df_test)} IPOs")
    print()

    # 6. Evaluate backtest performance
    print("=" * 80)
    print("BACKTEST PERFORMANCE (2024 H2)")
    print("=" * 80)
    print()

    backtest_results = {}

    for target_name in ["day0_high", "day0_close", "day1_close"]:
        y_true = y_test_dict[target_name]
        y_pred = predictions[target_name]

        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        backtest_results[target_name] = {
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
            "mape": mape,
        }

        print(f"Target: {target_name}")
        print("-" * 80)
        print(f"  MAE:  {mae:>10,.2f} KRW")
        print(f"  RMSE: {rmse:>10,.2f} KRW")
        print(f"  R²:   {r2:>10.4f}")
        print(f"  MAPE: {mape:>10.2f}%")
        print()

    # 7. Create detailed comparison
    print("=" * 80)
    print("CREATING DETAILED COMPARISON")
    print("=" * 80)

    comparison = pd.DataFrame({
        "company_name": df_test["company_name"].values,
        "code": df_test["code"].values,
        "listing_date": df_test["listing_date"].values,
        "ipo_price_confirmed": df_test["ipo_price_confirmed"].values,
        # Actual
        "actual_day0_high": y_test_dict["day0_high"],
        "actual_day0_close": y_test_dict["day0_close"],
        "actual_day1_close": y_test_dict["day1_close"],
        # Predicted
        "predicted_day0_high": predictions["day0_high"],
        "predicted_day0_close": predictions["day0_close"],
        "predicted_day1_close": predictions["day1_close"],
    })

    # Calculate errors
    comparison["error_day0_high"] = comparison["predicted_day0_high"] - comparison["actual_day0_high"]
    comparison["error_day0_close"] = comparison["predicted_day0_close"] - comparison["actual_day0_close"]
    comparison["error_day1_close"] = comparison["predicted_day1_close"] - comparison["actual_day1_close"]

    # Calculate returns
    comparison["actual_day0_return"] = (
        (comparison["actual_day0_close"] - comparison["ipo_price_confirmed"]) /
        comparison["ipo_price_confirmed"] * 100
    )
    comparison["predicted_day0_return"] = (
        (comparison["predicted_day0_close"] - comparison["ipo_price_confirmed"]) /
        comparison["ipo_price_confirmed"] * 100
    )

    # Save
    output_file = "reports/backtest_2024h2_comparison.csv"
    comparison.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"✅ Saved detailed comparison: {output_file}")
    print()

    # 8. Show best/worst predictions
    print("=" * 80)
    print("BEST PREDICTIONS (Lowest Absolute Error)")
    print("=" * 80)

    comparison["abs_error_day0_close"] = comparison["error_day0_close"].abs()

    best = comparison.nsmallest(5, "abs_error_day0_close")[
        ["company_name", "listing_date", "actual_day0_close", "predicted_day0_close", "error_day0_close"]
    ]
    print(best.to_string(index=False))
    print()

    print("=" * 80)
    print("WORST PREDICTIONS (Highest Absolute Error)")
    print("=" * 80)

    worst = comparison.nlargest(5, "abs_error_day0_close")[
        ["company_name", "listing_date", "actual_day0_close", "predicted_day0_close", "error_day0_close"]
    ]
    print(worst.to_string(index=False))
    print()

    # 9. Investment simulation
    print("=" * 80)
    print("INVESTMENT SIMULATION")
    print("=" * 80)
    print()

    # Strategy 1: Invest in top 10 predicted returns
    comparison_sorted = comparison.sort_values("predicted_day0_return", ascending=False)
    top10 = comparison_sorted.head(10)

    avg_predicted_return = top10["predicted_day0_return"].mean()
    avg_actual_return = top10["actual_day0_return"].mean()

    print("Strategy 1: 예측 수익률 상위 10개 종목 청약")
    print("-" * 80)
    print(f"  예측 평균 수익률: {avg_predicted_return:>10.2f}%")
    print(f"  실제 평균 수익률: {avg_actual_return:>10.2f}%")
    print(f"  예측 오차:       {abs(avg_predicted_return - avg_actual_return):>10.2f}%p")
    print()

    print("상위 10개 종목:")
    print(top10[["company_name", "listing_date", "predicted_day0_return", "actual_day0_return"]].to_string(index=False))
    print()

    # Strategy 2: Only invest if predicted return > 20%
    high_return = comparison[comparison["predicted_day0_return"] > 20]

    if len(high_return) > 0:
        avg_predicted_high = high_return["predicted_day0_return"].mean()
        avg_actual_high = high_return["actual_day0_return"].mean()

        print("Strategy 2: 예측 수익률 20% 이상 종목만 청약")
        print("-" * 80)
        print(f"  대상 종목 수:      {len(high_return)}개")
        print(f"  예측 평균 수익률: {avg_predicted_high:>10.2f}%")
        print(f"  실제 평균 수익률: {avg_actual_high:>10.2f}%")
        print(f"  승률 (수익 발생):  {(high_return['actual_day0_return'] > 0).mean() * 100:>10.2f}%")
        print()
    else:
        print("Strategy 2: 예측 수익률 20% 이상 종목 없음")
        print()

    # 10. Summary
    print("=" * 80)
    print("BACKTEST SUMMARY")
    print("=" * 80)
    print()

    print(f"Test period: 2024-07-01 ~ 2024-12-26")
    print(f"Test samples: {len(df_test)} IPOs")
    print()

    print("Performance:")
    for target_name, metrics in backtest_results.items():
        print(f"  {target_name:15}: R² {metrics['r2']:.4f}, MAE {metrics['mae']:>8,.0f}원")

    print()
    print("Investment simulation:")
    print(f"  Top 10 predicted: 예측 {avg_predicted_return:.1f}% → 실제 {avg_actual_return:.1f}%")

    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
