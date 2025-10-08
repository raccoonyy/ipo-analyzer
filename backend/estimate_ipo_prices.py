"""
Estimate actual IPO prices from day0 trading data
Replace par value placeholders with estimated IPO prices
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


def estimate_ipo_price(row):
    """
    Estimate IPO price from day0 trading data

    Strategy:
    - Use day0_low_kis as the best estimate (usually closest to IPO price)
    - Fallback to day0_open_kis / 1.5 if low is missing
    - Keep par value if no trading data available

    Args:
        row: DataFrame row with trading data

    Returns:
        Estimated IPO price
    """
    # Current (incorrect) price - par value
    current_price = row.get("ipo_price_confirmed", 0)

    # Try day0_low first (most conservative estimate)
    day0_low = row.get("day0_low_kis", 0)
    if pd.notna(day0_low) and day0_low > 0:
        return day0_low

    # Fallback to day0_open / 1.5 (assume average 50% first day gain)
    day0_open = row.get("day0_open_kis", 0)
    if pd.notna(day0_open) and day0_open > 0:
        return day0_open / 1.5

    # If no trading data, keep current value (par value)
    return current_price


def update_dataset_with_estimates(dataset_file: Path) -> bool:
    """
    Update dataset with estimated IPO prices

    Args:
        dataset_file: Path to dataset CSV file

    Returns:
        True if updated successfully
    """
    if not dataset_file.exists():
        logger.warning(f"Dataset not found: {dataset_file}")
        return False

    logger.info(f"Updating {dataset_file.name}...")

    # Load dataset
    df = pd.read_csv(dataset_file)

    # Store original par value
    if "par_value" not in df.columns:
        df["par_value"] = df["ipo_price_confirmed"]

    # Estimate IPO prices
    df["estimated_ipo_price"] = df.apply(estimate_ipo_price, axis=1)

    # Count how many were updated
    par_values = df["ipo_price_confirmed"]
    estimated_values = df["estimated_ipo_price"]

    # Updated = where estimated is different from par value
    updated_mask = (estimated_values != par_values) & (estimated_values > 1000)
    updated_count = updated_mask.sum()
    total_count = len(df)

    logger.info(
        f"  Updated {updated_count}/{total_count} IPOs ({updated_count/total_count*100:.1f}%)"
    )

    # Show sample updates
    if updated_count > 0:
        logger.info("\n  Sample updates:")
        samples = df[updated_mask].head(5)
        for idx, row in samples.iterrows():
            logger.info(
                f"    {row['company_name']:25} ({row['code']}): "
                f"{int(row['par_value']):>6}원 → {int(row['estimated_ipo_price']):>10,}원"
            )

    # Update all IPO price fields
    df["ipo_price_lower"] = df["estimated_ipo_price"]
    df["ipo_price_upper"] = df["estimated_ipo_price"]
    df["ipo_price_confirmed"] = df["estimated_ipo_price"]

    # Remove temporary column
    df = df.drop(columns=["estimated_ipo_price"])

    # Save updated dataset
    df.to_csv(dataset_file, index=False, encoding="utf-8-sig")

    logger.info(f"✅ Updated {dataset_file.name}")

    return True


def main():
    """Update all datasets with estimated IPO prices"""
    print("=" * 80)
    print("ESTIMATE IPO PRICES FROM DAY0 TRADING DATA")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("Strategy:")
    print("  - Use day0_low_kis as IPO price estimate (most conservative)")
    print("  - Fallback to day0_open_kis / 1.5 if low is missing")
    print("  - Original par values saved to 'par_value' column")
    print()

    # Update datasets
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

        if update_dataset_with_estimates(dataset_file):
            updated += 1

        print()

    # Summary
    print("=" * 80)
    print("UPDATE COMPLETE")
    print("=" * 80)

    print(f"Updated {updated} dataset(s)")
    print()
    print("⚠️  NOTE: These are ESTIMATES based on day0 trading data")
    print("   Real IPO prices should be collected from KIS API later")
    print()
    print("Next steps:")
    print("  1. Run train_model.py to retrain with estimated prices")
    print("  2. Run generate_frontend_predictions.py to update predictions")
    print("  3. Later: Run collect_ipo_prices.py to get actual IPO prices from KIS API")
    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    main()
