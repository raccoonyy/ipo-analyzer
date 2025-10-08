"""
Fix feature_names.pkl to match the model (26 features without financial metrics)
"""

import pickle
from pathlib import Path

# Correct feature names (26 features, without listing_per/pbr/eps)
correct_feature_names = [
    "ipo_price_confirmed",
    "shares_offered",
    "institutional_demand_rate",
    "lockup_ratio",
    "subscription_competition_rate",
    "market_cap_ratio",
    "total_offering_value",
    "ipo_price_range_pct",
    "price_positioning",
    "demand_to_lockup_ratio",
    "allocation_balance",
    "high_competition",
    "high_demand",
    "listing_month",
    "listing_quarter",
    "listing_day_of_week",
    "listing_method_encoded",
    "industry_encoded",
    "theme_encoded",
    "day0_volume_kis",
    "day0_trading_value",
    "day1_volume",
    "day1_trading_value",
    "day0_turnover_rate",
    "day1_turnover_rate",
    "day0_volatility",
]

def main():
    print("=" * 80)
    print("FIXING FEATURE NAMES")
    print("=" * 80)
    print()

    feature_file = Path("data/processed/feature_names.pkl")

    # Load current feature names
    with open(feature_file, "rb") as f:
        current_names = pickle.load(f)

    print(f"Current feature count: {len(current_names)}")
    print(f"Correct feature count: {len(correct_feature_names)}")
    print()

    # Save correct feature names
    with open(feature_file, "wb") as f:
        pickle.dump(correct_feature_names, f)

    print(f"✅ Updated {feature_file}")
    print(f"   Features: {len(correct_feature_names)}")
    print()


if __name__ == "__main__":
    main()
