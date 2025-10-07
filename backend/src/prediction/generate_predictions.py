"""
Generate Static Predictions for Frontend
Precompute predictions for all IPOs and save to JSON file
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import List, Dict
import sys
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data_collection.ipo_collector import IPODataCollector
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor
from src.config import settings

logger = logging.getLogger(__name__)


class PredictionGenerator:
    """Generate and save precomputed predictions for frontend consumption"""

    def __init__(
        self, models_dir: str = "models", transformers_dir: str = "data/processed"
    ):
        self.models_dir = Path(models_dir)
        self.transformers_dir = Path(transformers_dir)

        # Load models and transformers
        self.predictor = IPOPricePredictor()
        self.predictor.load_models(models_dir)

        self.engineer = IPOFeatureEngineer()
        self.engineer.load_transformers(transformers_dir)

    def generate_predictions_for_dataset(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate predictions for a dataset of IPOs

        Args:
            df: DataFrame with IPO metadata (without actual price data)

        Returns:
            List of prediction dictionaries
        """
        # Engineer features (without fitting)
        features_df = self.engineer.engineer_features(df, fit=False)
        X = features_df[self.engineer.feature_names].values

        # Generate predictions
        predictions = self.predictor.predict(X)

        # Format results
        results = []
        for idx, row in df.iterrows():
            prediction_dict = {
                "company_name": row["company_name"],
                "code": row["code"],
                "listing_date": (
                    row["listing_date"].strftime("%Y-%m-%d")
                    if isinstance(row["listing_date"], pd.Timestamp)
                    else row["listing_date"]
                ),
                "ipo_price": int(row["ipo_price_confirmed"]),
                "predicted": {
                    "day0_high": int(round(predictions["day0_high"][idx])),
                    "day0_close": int(round(predictions["day0_close"][idx])),
                    "day1_close": int(round(predictions["day1_close"][idx])),
                },
                "metadata": {
                    "shares_offered": int(row["shares_offered"]),
                    "institutional_demand_rate": float(
                        row["institutional_demand_rate"]
                    ),
                    "subscription_competition_rate": float(
                        row["subscription_competition_rate"]
                    ),
                    "industry": row["industry"],
                    "theme": row["theme"],
                },
            }

            # Add actual values if available (for model validation)
            if "day0_high" in df.columns and pd.notna(row.get("day0_high")):
                prediction_dict["actual"] = {
                    "day0_high": int(row["day0_high"]),
                    "day0_close": int(row["day0_close"]),
                    "day1_close": int(row["day1_close"]),
                }

            results.append(prediction_dict)

        return results

    def generate_and_save(
        self,
        start_year: int = None,
        end_year: int = None,
        output_file: str = None,
    ):
        """
        Generate predictions and save to JSON file

        Args:
            start_year: Start year for IPO data (default: from settings)
            end_year: End year for IPO data (default: from settings)
            output_file: Output JSON file path (default: from settings)
        """
        # Use settings defaults if not provided
        if start_year is None:
            start_year = settings.DATA_START_YEAR
        if end_year is None:
            end_year = settings.DATA_END_YEAR
        if output_file is None:
            output_file = settings.PREDICTION_OUTPUT_FILE

        logger.info(
            f"Generating predictions for IPOs from {start_year} to {end_year}..."
        )

        # Collect IPO data
        collector = IPODataCollector()
        df = collector.collect_ipo_metadata(start_year, end_year)

        # Generate predictions
        predictions = self.generate_predictions_for_dataset(df)

        # Save to JSON
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(predictions)} predictions to {output_path}")

        # Generate summary statistics
        self._print_summary(predictions)

        return predictions

    def _print_summary(self, predictions: List[Dict]):
        """Print summary statistics of predictions"""
        print("\n" + "=" * 60)
        print("PREDICTION SUMMARY")
        print("=" * 60)

        total_ipos = len(predictions)
        print(f"Total IPOs: {total_ipos}")

        # Calculate statistics
        day0_highs = [p["predicted"]["day0_high"] for p in predictions]
        day0_closes = [p["predicted"]["day0_close"] for p in predictions]
        day1_closes = [p["predicted"]["day1_close"] for p in predictions]

        print(f"\nDay 0 High Price:")
        print(f"  Mean: ₩{np.mean(day0_highs):,.0f}")
        print(f"  Median: ₩{np.median(day0_highs):,.0f}")
        print(f"  Range: ₩{np.min(day0_highs):,.0f} - ₩{np.max(day0_highs):,.0f}")

        print(f"\nDay 0 Close Price:")
        print(f"  Mean: ₩{np.mean(day0_closes):,.0f}")
        print(f"  Median: ₩{np.median(day0_closes):,.0f}")
        print(f"  Range: ₩{np.min(day0_closes):,.0f} - ₩{np.max(day0_closes):,.0f}")

        print(f"\nDay 1 Close Price:")
        print(f"  Mean: ₩{np.mean(day1_closes):,.0f}")
        print(f"  Median: ₩{np.median(day1_closes):,.0f}")
        print(f"  Range: ₩{np.min(day1_closes):,.0f} - ₩{np.max(day1_closes):,.0f}")

        # If actual values exist, calculate accuracy
        if "actual" in predictions[0]:
            self._calculate_accuracy(predictions)

        print("=" * 60)

    def _calculate_accuracy(self, predictions: List[Dict]):
        """Calculate prediction accuracy if actual values are available"""
        print("\nMODEL ACCURACY:")

        for target in ["day0_high", "day0_close", "day1_close"]:
            actual = [p["actual"][target] for p in predictions if "actual" in p]
            predicted = [p["predicted"][target] for p in predictions if "actual" in p]

            if len(actual) > 0:
                mae = np.mean(np.abs(np.array(actual) - np.array(predicted)))
                mape = (
                    np.mean(
                        np.abs(
                            (np.array(actual) - np.array(predicted)) / np.array(actual)
                        )
                    )
                    * 100
                )

                print(f"  {target}:")
                print(f"    MAE: ₩{mae:,.0f}")
                print(f"    MAPE: {mape:.2f}%")


def main():
    """Main execution function"""
    print("=" * 60)
    print("IPO PREDICTION GENERATOR")
    print("=" * 60)

    # Check if models exist
    models_path = Path("models")
    if not models_path.exists() or not list(models_path.glob("model_*.pkl")):
        print("\n⚠ Warning: Trained models not found!")
        print("Please run model training first:")
        print("  python src/models/ipo_predictor.py")
        print("\nGenerating sample predictions with placeholder models...")

        # For demonstration, we'll train on sample data
        from src.data_collection.ipo_collector import IPODataCollector
        from src.features.feature_engineering import IPOFeatureEngineer
        from src.models.ipo_predictor import IPOPricePredictor

        collector = IPODataCollector()
        df = collector.collect_full_dataset(2022, 2025)

        engineer = IPOFeatureEngineer()
        X, y_dict, metadata = engineer.prepare_training_data(df)

        predictor = IPOPricePredictor(model_type="random_forest")
        predictor.train(X, y_dict)

        predictor.save_models()
        engineer.save_transformers()

    # Generate predictions (uses settings defaults)
    generator = PredictionGenerator()
    predictions = generator.generate_and_save()

    print("\n✓ Prediction generation complete!")
    print(f"Frontend can now consume: {settings.PREDICTION_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
