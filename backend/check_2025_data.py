"""Check 2025 data across all datasets"""
import pandas as pd

# Check offering data
offering = pd.read_csv("data/raw/ipo_offering_info.csv")
offering['year'] = offering['listing_date'].str[:4]
print("=== IPO Offering Data (KIS API) ===")
print(offering['year'].value_counts().sort_index())
print(f"\nTotal: {len(offering)}")
print(f"\n2025 IPOs: {len(offering[offering['year'] == '2025'])}")

# Sample 2025 IPOs
print("\nSample 2025 IPOs from offering data:")
print(offering[offering['year'] == '2025'][['code', 'listing_date', 'ipo_price']].head(10))

# Check main dataset
print("\n" + "="*80)
print("=== Main Dataset ===")
try:
    main = pd.read_csv("data/raw/ipo_full_dataset_2022_2024.csv")
    main['listing_date'] = pd.to_datetime(main['listing_date'])
    main['year'] = main['listing_date'].dt.year
    print(main['year'].value_counts().sort_index())
    print(f"\nTotal: {len(main)}")

    # Check if any 2025 data
    main_2025 = main[main['year'] == 2025]
    print(f"\n2025 IPOs in main dataset: {len(main_2025)}")
except Exception as e:
    print(f"Error: {e}")

# Check enhanced dataset
print("\n" + "="*80)
print("=== Enhanced Dataset ===")
try:
    enhanced = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")
    enhanced['listing_date'] = pd.to_datetime(enhanced['listing_date'])
    enhanced['year'] = enhanced['listing_date'].dt.year
    print(enhanced['year'].value_counts().sort_index())
    print(f"\nTotal: {len(enhanced)}")

    # Check if any 2025 data
    enhanced_2025 = enhanced[enhanced['year'] == 2025]
    print(f"\n2025 IPOs in enhanced dataset: {len(enhanced_2025)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"KIS Offering API (2025): 68 IPOs")
print(f"Main dataset (2025): {len(main_2025) if 'main_2025' in locals() else 'N/A'}")
print(f"Enhanced dataset (2025): {len(enhanced_2025) if 'enhanced_2025' in locals() else 'N/A'}")
print("\nNote: The main dataset is named '2022_2024' so it shouldn't contain 2025 data.")
print("The 68 2025 IPOs exist only in the KIS offering data (ipo_offering_info.csv).")
