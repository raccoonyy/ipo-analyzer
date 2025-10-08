"""
Update Pipeline - One Command Update
Runs all incremental update steps in sequence
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """
    Run a command and return success status

    Args:
        command: Command to run
        description: Description for logging

    Returns:
        True if successful, False otherwise
    """
    print()
    print("=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)
    print(f"Command: {command}")
    print()

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=Path(__file__).parent,
        )
        print()
        print(f"✅ {description} - SUCCESS")
        return True

    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ {description} - FAILED")
        print(f"Error code: {e.returncode}")
        return False


def main():
    """Run complete incremental update pipeline"""
    print("=" * 80)
    print("IPO ANALYZER - INCREMENTAL UPDATE PIPELINE")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("This script will:")
    print("  1. Collect new IPO metadata (KRX API)")
    print("  2. Collect daily indicators for new IPOs (KIS API)")
    print("  3. Merge indicators into enhanced dataset")
    print("  4. Retrain ML model with updated data")
    print("  5. Generate frontend predictions JSON")
    print()

    # Track success
    steps = []

    # Step 1: Collect new IPO data
    success = run_command(
        "uv run python collect_incremental_data.py",
        "Collect new IPO metadata"
    )
    steps.append(("Collect IPO metadata", success))

    if not success:
        print()
        print("⚠️  IPO metadata collection failed or no new data.")
        print("Continuing with other steps...")
        print()

    # Step 2: Collect daily indicators
    success = run_command(
        "uv run python collect_daily_indicators_incremental.py",
        "Collect daily indicators (KIS API)"
    )
    steps.append(("Collect daily indicators", success))

    if not success:
        print()
        print("❌ Daily indicators collection failed.")
        print("Cannot continue without this data.")
        print()
        print_summary(steps)
        return

    # Step 3: Merge indicators
    success = run_command(
        "uv run python merge_indicators.py",
        "Merge indicators into enhanced dataset"
    )
    steps.append(("Merge indicators", success))

    if not success:
        print()
        print("❌ Indicator merge failed.")
        print("Cannot continue without merged data.")
        print()
        print_summary(steps)
        return

    # Step 4: Retrain model
    success = run_command(
        "uv run python train_model.py",
        "Retrain ML model"
    )
    steps.append(("Retrain model", success))

    if not success:
        print()
        print("❌ Model training failed.")
        print("Cannot generate predictions.")
        print()
        print_summary(steps)
        return

    # Step 5: Generate frontend predictions
    success = run_command(
        "uv run python generate_frontend_predictions.py",
        "Generate frontend predictions JSON"
    )
    steps.append(("Generate frontend JSON", success))

    # Summary
    print()
    print_summary(steps)

    print()
    print("=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if all succeeded
    all_success = all(success for _, success in steps)

    if all_success:
        print("✅ All steps completed successfully!")
        print()
        print("Frontend data has been updated:")
        print("  ../frontend/public/ipo_precomputed.json")
        print()
    else:
        print("⚠️  Some steps failed. Please review the output above.")
        print()


def print_summary(steps):
    """Print summary of pipeline execution"""
    print()
    print("=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)

    for i, (step_name, success) in enumerate(steps, 1):
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{i}. {step_name:35} : {status}")


if __name__ == "__main__":
    main()
