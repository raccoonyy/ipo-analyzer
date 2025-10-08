"""
Update IPO datasets with actual IPO prices from KIS API
Replace par value placeholders with real IPO offering prices
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_offering_data() -> pd.DataFrame:
    """Load IPO offering info from CSV"""
    offering_file = Path("data/raw/ipo_offering_info.csv")

    if not offering_file.exists():
        raise FileNotFoundError(
            f"IPO offering data not found: {offering_file}\n"
            "Please run collect_ipo_prices.py first"
        )

    df = pd.read_csv(offering_file)

    # Ensure code is string and padded
    df["code"] = df["code"].astype(str).str.zfill(6)

    logger.info(f"Loaded {len(df)} IPO offering records")

    return df


def update_dataset(dataset_file: Path, offering_df: pd.DataFrame) -> bool:
    """
    Update a dataset file with actual IPO prices

    Args:
        dataset_file: Path to dataset CSV file
        offering_df: DataFrame with actual IPO prices

    Returns:
        True if updated successfully
    """
    if not dataset_file.exists():
        logger.warning(f"Dataset not found: {dataset_file}")
        return False

    logger.info(f"Updating {dataset_file.name}...")

    # Load dataset
    df = pd.read_csv(dataset_file)

    # Ensure code is string and padded
    df["code"] = df["code"].astype(str).str.zfill(6)

    # Store original par value before overwriting
    if "par_value" not in df.columns:
        df["par_value"] = df["ipo_price_confirmed"]

    # Merge with offering data
    df_merged = df.merge(offering_df[["code", "ipo_price"]], on="code", how="left")

    # Count matches
    matched = df_merged["ipo_price"].notna().sum()
    total = len(df_merged)

    logger.info(f"  Matched {matched}/{total} IPOs ({matched/total*100:.1f}%)")

    # Update IPO price fields with actual prices
    mask = df_merged["ipo_price"].notna()

    df.loc[mask, "ipo_price_lower"] = df_merged.loc[mask, "ipo_price"]
    df.loc[mask, "ipo_price_upper"] = df_merged.loc[mask, "ipo_price"]
    df.loc[mask, "ipo_price_confirmed"] = df_merged.loc[mask, "ipo_price"]

    # Show some examples of updates
    if matched > 0:
        logger.info("\n  Sample updates:")
        sample = df_merged[mask].head(5)
        for idx, row in sample.iterrows():
            logger.info(
                f"    {row['company_name']:20} ({row['code']}): "
                f"{int(row['par_value']):>6}원 → {int(row['ipo_price']):>10,}원"
            )

    # Save updated dataset
    df.to_csv(dataset_file, index=False, encoding="utf-8-sig")

    logger.info(f"✅ Updated {dataset_file.name}")

    return True


def main():
    """Update all IPO datasets with actual prices"""
    print("=" * 80)
    print("UPDATE IPO DATASETS WITH ACTUAL PRICES")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Load offering data
    print("=" * 80)
    print("LOADING IPO OFFERING DATA")
    print("=" * 80)

    try:
        offering_df = load_offering_data()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    print(f"✅ Loaded {len(offering_df)} offering records")
    print()

    # Show price statistics
    print("IPO Price statistics:")
    print(f"  Min:    {offering_df['ipo_price'].min():>12,.0f}원")
    print(f"  Max:    {offering_df['ipo_price'].max():>12,.0f}원")
    print(f"  Mean:   {offering_df['ipo_price'].mean():>12,.0f}원")
    print(f"  Median: {offering_df['ipo_price'].median():>12,.0f}원")
    print()

    # 2. Update datasets
    print("=" * 80)
    print("UPDATING DATASETS")
    print("=" * 80)

    data_dir = Path("data/raw")

    datasets = [
        "ipo_full_dataset_2022_2024.csv",
        "ipo_full_dataset_2022_2024_enhanced.csv",
        "ipo_full_dataset_2022_2024_complete.csv",
    ]

    updated = 0
    for dataset_name in datasets:
        dataset_file = data_dir / dataset_name

        if update_dataset(dataset_file, offering_df):
            updated += 1

        print()

    # 3. Summary
    print("=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)

    print(f"Updated {updated} dataset(s)")
    print()
    print("Next steps:")
    print("  1. Run train_model.py to retrain with corrected prices")
    print("  2. Run generate_frontend_predictions.py to update predictions")
    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
