"""
Train IPO Price Prediction Model
Uses complete dataset (226 IPOs from 2022-2024)
"""

import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Train IPO price prediction models"""
    parser = argparse.ArgumentParser(description="Train IPO prediction model")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/raw/ipo_full_dataset_2022_2024_enhanced.csv",
        help="Path to training data CSV file",
    )
    args = parser.parse_args()

    print("=" * 80)
    print("IPO PRICE PREDICTION MODEL TRAINING")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Load complete dataset
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    input_file = args.data_path
    df = pd.read_csv(input_file)

    print(f"Loaded {len(df)} enhanced IPO records (with KIS API indicators)")
    print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")
    print()

    # Filter out SPAC companies
    initial_count = len(df)
    df = df[
        (~df["company_name"].str.contains("기업인수목적", na=False))
        & (
            ~df.get("industry", pd.Series([""] * len(df))).str.contains(
                "SPAC", na=False
            )
        )
    ]
    spac_count = initial_count - len(df)
    if spac_count > 0:
        print(f"Filtered out {spac_count} SPAC companies")
        print(f"Remaining IPOs: {len(df)}")
        print()

    # 2. Feature engineering
    print("=" * 80)
    print("FEATURE ENGINEERING")
    print("=" * 80)

    engineer = IPOFeatureEngineer()
    X, y_dict, metadata = engineer.prepare_training_data(df)

    print(f"Feature matrix shape: {X.shape}")
    print(f"Number of features: {len(engineer.feature_names)}")
    print(f"Target variables: {list(y_dict.keys())}")
    print()

    print("Features used:")
    for i, feature in enumerate(engineer.feature_names, 1):
        print(f"  {i:2}. {feature}")
    print()

    # 3. Train models
    print("=" * 80)
    print("TRAINING MODELS")
    print("=" * 80)
    print(f"Model type: Random Forest")
    print(f"Train/test split: 80/20")
    print(f"Training samples: ~{int(len(X) * 0.8)}")
    print(f"Test samples: ~{int(len(X) * 0.2)}")
    print()

    predictor = IPOPricePredictor(model_type="random_forest")
    results = predictor.train(X, y_dict, test_size=0.2)

    # 4. Display results
    print()
    print("=" * 80)
    print("TRAINING RESULTS")
    print("=" * 80)
    print()

    for target_name, metrics in results.items():
        print(f"Target: {target_name}")
        print("-" * 80)

        train_metrics = metrics["train"]
        test_metrics = metrics["test"]

        print(f"  Training Set:")
        print(f"    MAE:  {train_metrics['mae']:>10,.2f} KRW")
        print(f"    RMSE: {train_metrics['rmse']:>10,.2f} KRW")
        print(f"    R²:   {train_metrics['r2']:>10.4f}")
        print(f"    MAPE: {train_metrics['mape']:>10.2f}%")
        print()

        print(f"  Test Set:")
        print(f"    MAE:  {test_metrics['mae']:>10,.2f} KRW")
        print(f"    RMSE: {test_metrics['rmse']:>10,.2f} KRW")
        print(f"    R²:   {test_metrics['r2']:>10.4f}")
        print(f"    MAPE: {test_metrics['mape']:>10.2f}%")
        print()

    # 5. Feature importance
    print("=" * 80)
    print("FEATURE IMPORTANCE (Top 10)")
    print("=" * 80)
    print()

    for target_name in ["day0_high", "day0_close", "day1_close"]:
        print(f"Target: {target_name}")
        print("-" * 80)

        importance_df = predictor.get_feature_importance(
            engineer.feature_names, target_name, top_n=10
        )

        if importance_df is not None:
            for idx, row in importance_df.iterrows():
                print(f"  {row['feature']:30} : {row['importance']:.4f}")
        print()

    # 6. Save models and transformers
    print("=" * 80)
    print("SAVING MODELS")
    print("=" * 80)

    predictor.save_models("models")
    engineer.save_transformers("data/processed")

    print("✅ Saved trained models to: models/")
    print("✅ Saved transformers to: data/processed/")
    print()

    # 7. Summary
    print("=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Models trained:")
    for target in ["day0_high", "day0_close", "day1_close"]:
        print(f"  - models/model_{target}.pkl")
    print()
    print("Transformers saved:")
    print(f"  - data/processed/scaler.pkl")
    print(f"  - data/processed/label_encoders.pkl")
    print(f"  - data/processed/feature_names.pkl")
    print()
    print("Next steps:")
    print("  1. Review model performance metrics above")
    print("  2. Use src/prediction/generate_predictions.py to generate predictions")
    print("  3. Deploy models for production use")
    print()


if __name__ == "__main__":
    main()
