"""
Generate Predictions for Frontend
Create JSON file with all IPO predictions for frontend visualization
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from src.features.feature_engineering import IPOFeatureEngineer
from src.models.ipo_predictor import IPOPricePredictor
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def calculate_returns(row):
    """Calculate various return metrics"""
    ipo_price = row["ipo_price_confirmed"]
    day0_close = row["predicted_day0_close"]
    day1_close = row["predicted_day1_close"]

    # Day0→Day1 change
    day0_to_day1_return = (
        ((day1_close - day0_close) / day0_close * 100) if day0_close > 0 else 0
    )

    returns = {
        "day0_high_return": (
            (row["predicted_day0_high"] - ipo_price) / ipo_price * 100
        ),
        "day0_close_return": ((day0_close - ipo_price) / ipo_price * 100),
        "day1_close_return": day0_to_day1_return,  # Day0 close relative
        "day0_to_day1_return": day0_to_day1_return,  # Day0→Day1 change (same as above)
    }

    # Actual returns
    if pd.notna(row.get("actual_day0_high")):
        actual_day0_close = row["actual_day0_close"]
        actual_day1_close = row["actual_day1_close"]

        actual_day0_to_day1_return = (
            ((actual_day1_close - actual_day0_close) / actual_day0_close * 100)
            if actual_day0_close > 0
            else 0
        )

        returns["actual_day0_high_return"] = (
            (row["actual_day0_high"] - ipo_price) / ipo_price * 100
        )
        returns["actual_day0_close_return"] = (
            (actual_day0_close - ipo_price) / ipo_price * 100
        )
        returns["actual_day1_close_return"] = (
            actual_day0_to_day1_return  # Day0 close relative
        )
        returns["actual_day0_to_day1_return"] = actual_day0_to_day1_return

    return returns


def format_ipo_record(row, index):
    """Format single IPO record for frontend"""
    returns = calculate_returns(row)

    # Basic info
    record = {
        "id": int(index),
        "company_name": str(row["company_name"]),
        "code": str(row["code"]).zfill(6),
        "listing_date": str(row["listing_date"])[:10],  # YYYY-MM-DD
        "industry": str(row.get("industry", "N/A")),
        "theme": str(row.get("theme", "N/A")),
        "sector_38": (
            str(row.get("sector_38", "N/A"))
            if pd.notna(row.get("sector_38"))
            else "N/A"
        ),
        # IPO details
        "ipo_price_lower": int(row["ipo_price_lower"]),
        "ipo_price_upper": int(row["ipo_price_upper"]),
        "ipo_price_confirmed": int(row["ipo_price_confirmed"]),
        "shares_offered": int(row["shares_offered"]),
        # Subscription metrics
        "institutional_demand_rate": float(row.get("institutional_demand_rate", 0)),
        "subscription_competition_rate": float(
            row.get("subscription_competition_rate", 0)
        ),
        "lockup_ratio": float(row.get("lockup_ratio", 0)),
        # Predictions
        "predicted_day0_high": int(round(row["predicted_day0_high"])),
        "predicted_day0_close": int(round(row["predicted_day0_close"])),
        "predicted_day1_close": int(round(row["predicted_day1_close"])),
        "predicted_day0_high_return": round(returns["day0_high_return"], 2),
        "predicted_day0_close_return": round(returns["day0_close_return"], 2),
        "predicted_day1_close_return": round(returns["day1_close_return"], 2),
        "predicted_day0_to_day1_return": round(returns["day0_to_day1_return"], 2),
    }

    # Actual values (if available)
    if pd.notna(row.get("actual_day0_high")):
        actual_day1_high = row.get("actual_day1_high", row.get("day1_high", 0))

        record["actual_day0_high"] = int(row["actual_day0_high"])
        record["actual_day0_close"] = int(row["actual_day0_close"])
        record["actual_day1_high"] = (
            int(actual_day1_high) if pd.notna(actual_day1_high) else 0
        )
        record["actual_day1_close"] = int(row["actual_day1_close"])
        record["actual_day0_high_return"] = round(returns["actual_day0_high_return"], 2)
        record["actual_day0_close_return"] = round(
            returns["actual_day0_close_return"], 2
        )
        record["actual_day1_close_return"] = round(
            returns["actual_day1_close_return"], 2
        )
        record["actual_day0_to_day1_return"] = round(
            returns["actual_day0_to_day1_return"], 2
        )

        # Calculate day1_high return (day0 close relative)
        if actual_day1_high > 0 and row["actual_day0_close"] > 0:
            record["actual_day1_high_return"] = round(
                (
                    (actual_day1_high - row["actual_day0_close"])
                    / row["actual_day0_close"]
                    * 100
                ),
                2,
            )

        # Prediction accuracy
        record["error_day0_close"] = int(
            row["predicted_day0_close"] - row["actual_day0_close"]
        )
        record["error_pct_day0_close"] = round(
            (row["predicted_day0_close"] - row["actual_day0_close"])
            / row["actual_day0_close"]
            * 100,
            2,
        )

    # OHLCV data for day0 (if available)
    if pd.notna(row.get("day0_open_kis")):
        record["day0_ohlcv"] = [
            {
                "timestamp": str(row["listing_date"])[:10],
                "open": int(row.get("day0_open_kis", 0)),
                "high": int(row.get("day0_high_kis", row.get("actual_day0_high", 0))),
                "low": int(row.get("day0_low_kis", 0)),
                "close": int(
                    row.get("day0_close_kis", row.get("actual_day0_close", 0))
                ),
                "volume": int(row.get("day0_volume_kis", 0)),
            }
        ]

    # OHLCV data for day1 (if available)
    if pd.notna(row.get("day1_open")):
        # Calculate day1 date (listing_date + 1 day)
        listing_date = pd.to_datetime(row["listing_date"])
        day1_date = listing_date + pd.Timedelta(days=1)

        record["day1_ohlcv"] = [
            {
                "timestamp": str(day1_date)[:10],
                "open": int(row.get("day1_open", 0)),
                "high": int(row.get("day1_high", 0)),
                "low": int(row.get("day1_low", 0)),
                "close": int(row.get("day1_close", row.get("actual_day1_close", 0))),
                "volume": int(row.get("day1_volume", 0)),
            }
        ]

    return record


def main():
    """Generate predictions JSON for frontend"""
    print("=" * 80)
    print("GENERATING FRONTEND PREDICTIONS JSON")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Load dataset
    print("=" * 80)
    print("LOADING DATA")
    print("=" * 80)

    input_file = "data/raw/ipo_full_dataset_2022_2025.csv"
    df = pd.read_csv(input_file)
    df["listing_date"] = pd.to_datetime(df["listing_date"])

    print(f"Loaded {len(df)} IPO records")
    print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")
    print()

    # Load sector data from 38.co.kr
    try:
        sector_data = pd.read_csv("data/raw/38_subscription_data.csv")
        df["code"] = df["code"].astype(str).str.zfill(6)
        sector_data["code"] = sector_data["code"].astype(str).str.zfill(6)
        df = df.merge(
            sector_data[["code", "sector_38"]],
            on="code",
            how="left",
        )
        sector_count = df["sector_38"].notna().sum()
        print(f"Merged sector data: {sector_count} IPOs have sector information")
        print()
    except FileNotFoundError:
        print("⚠️  Sector data not found, skipping sector merge")
        df["sector_38"] = None
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

    # 2. Load trained models
    print("=" * 80)
    print("LOADING MODELS")
    print("=" * 80)

    predictor = IPOPricePredictor(model_type="random_forest")
    predictor.load_models("models")

    engineer = IPOFeatureEngineer()
    engineer.load_transformers("data/processed")

    print("✅ Loaded models and transformers")
    print()

    # 3. Generate predictions
    print("=" * 80)
    print("GENERATING PREDICTIONS")
    print("=" * 80)

    features_df = engineer.engineer_features(df, fit=False)
    X = features_df[engineer.feature_names].values
    predictions = predictor.predict(X)

    print(f"✅ Generated predictions for {len(df)} IPOs")
    print()

    # 4. Create output DataFrame
    print("=" * 80)
    print("PREPARING OUTPUT DATA")
    print("=" * 80)

    output_df = df.copy()
    output_df["predicted_day0_high"] = predictions["day0_high"]
    output_df["predicted_day0_close"] = predictions["day0_close"]
    output_df["predicted_day1_close"] = predictions["day1_close"]

    # Rename actual values for clarity
    output_df["actual_day0_high"] = output_df["day0_high"]
    output_df["actual_day0_close"] = output_df["day0_close"]
    output_df["actual_day1_close"] = output_df["day1_close"]

    # Sort by listing date (newest first)
    output_df = output_df.sort_values("listing_date", ascending=False)

    print(f"✅ Prepared {len(output_df)} records")
    print()

    # 5. Convert to JSON format
    print("=" * 80)
    print("CONVERTING TO JSON")
    print("=" * 80)

    records = []
    for idx, row in output_df.iterrows():
        record = format_ipo_record(row, idx)
        records.append(record)

    # Create output structure
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "model_version": "v2.0",
            "total_ipos": len(records),
            "date_range": {
                "start": str(df["listing_date"].min())[:10],
                "end": str(df["listing_date"].max())[:10],
            },
            "features_used": engineer.feature_names,
            "model_type": "random_forest",
        },
        "ipos": records,
    }

    print(f"✅ Converted {len(records)} records to JSON format")
    print()

    # 6. Save to file
    print("=" * 80)
    print("SAVING JSON FILE")
    print("=" * 80)

    output_path = Path(settings.PREDICTION_OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    file_size = output_path.stat().st_size / 1024  # KB

    print(f"✅ Saved predictions to: {output_path}")
    print(f"   File size: {file_size:.2f} KB")
    print(f"   Total records: {len(records)}")
    print()

    # 7. Show sample
    print("=" * 80)
    print("SAMPLE OUTPUT (최근 5개 IPO)")
    print("=" * 80)

    for i, record in enumerate(records[:5], 1):
        print(f"\n{i}. {record['company_name']} ({record['code']})")
        print(f"   상장일: {record['listing_date']}")
        print(f"   공모가: {record['ipo_price_confirmed']:,}원")
        print(
            f"   예측 day0 종가: {record['predicted_day0_close']:,}원 ({record['predicted_day0_close_return']:+.1f}%)"
        )
        print(
            f"   예측 day1 종가: {record['predicted_day1_close']:,}원 ({record['predicted_day1_close_return']:+.1f}%)"
        )

        if "actual_day0_close" in record:
            print(
                f"   실제 day0 종가: {record['actual_day0_close']:,}원 ({record['actual_day0_close_return']:+.1f}%)"
            )
            print(
                f"   예측 오차: {record['error_day0_close']:+,}원 ({record['error_pct_day0_close']:+.1f}%)"
            )

    print()

    # 8. Summary statistics
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)

    # Filter records with actual values
    with_actuals = [r for r in records if "actual_day0_close" in r]

    if with_actuals:
        avg_error = np.mean([abs(r["error_day0_close"]) for r in with_actuals])
        avg_error_pct = np.mean([abs(r["error_pct_day0_close"]) for r in with_actuals])

        print(f"Records with actual values: {len(with_actuals)}/{len(records)}")
        print(f"Average prediction error: {avg_error:,.0f}원 ({avg_error_pct:.1f}%)")
        print()

    # Predicted returns distribution
    predicted_returns = [r["predicted_day0_close_return"] for r in records]
    print(f"Predicted day0 returns:")
    print(f"  Min:    {min(predicted_returns):>8.1f}%")
    print(f"  Max:    {max(predicted_returns):>8.1f}%")
    print(f"  Mean:   {np.mean(predicted_returns):>8.1f}%")
    print(f"  Median: {np.median(predicted_returns):>8.1f}%")
    print()

    # Industry distribution
    industries = {}
    for r in records:
        industry = r["industry"]
        industries[industry] = industries.get(industry, 0) + 1

    print("Industry distribution (Top 5):")
    for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True)[
        :5
    ]:
        print(f"  {industry:30}: {count:3}개 ({count/len(records)*100:.1f}%)")

    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Frontend can now use:")
    print(f"  {output_path}")
    print()


if __name__ == "__main__":
    main()
