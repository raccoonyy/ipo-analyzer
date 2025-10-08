"""
Validate OHLCV data consistency between KIS API and yfinance

This script compares:
1. 2022-2024 data: KIS data (from enhanced dataset) vs yfinance data
2. 2025 data: KIS data vs yfinance data
"""

import pandas as pd
import numpy as np


def compare_values(kis_val, yf_val, field_name, tolerance=0.01):
    """
    Compare two values with tolerance

    Args:
        kis_val: KIS value
        yf_val: yfinance value
        field_name: field name for reporting
        tolerance: relative tolerance (default 1%)

    Returns:
        dict with comparison results
    """
    if pd.isna(kis_val) and pd.isna(yf_val):
        return {"match": True, "status": "both_missing"}

    if pd.isna(kis_val):
        return {"match": False, "status": "kis_missing", "yf_val": yf_val}

    if pd.isna(yf_val):
        return {"match": False, "status": "yf_missing", "kis_val": kis_val}

    # Compare with relative tolerance
    diff = abs(kis_val - yf_val)
    rel_diff = diff / max(kis_val, yf_val) if max(kis_val, yf_val) > 0 else 0

    if rel_diff <= tolerance:
        return {
            "match": True,
            "status": "match",
            "kis_val": kis_val,
            "yf_val": yf_val,
            "diff": diff,
            "rel_diff_pct": rel_diff * 100,
        }
    else:
        return {
            "match": False,
            "status": "mismatch",
            "kis_val": kis_val,
            "yf_val": yf_val,
            "diff": diff,
            "rel_diff_pct": rel_diff * 100,
        }


def validate_2022_2024_data():
    """Validate 2022-2024 IPO data"""
    print("=" * 80)
    print("VALIDATING 2022-2024 IPO DATA (KIS vs yfinance)")
    print("=" * 80)
    print()

    # Load yfinance dataset (contains both KIS and yfinance data)
    df = pd.read_csv("data/raw/ipo_2022_2024_yfinance.csv")

    print(f"Dataset: {len(df)} IPOs")
    print()

    # Fields to compare
    fields_to_compare = [
        ("day0_high_kis", "day0_high_yf"),
        ("day0_close_kis", "day0_close_yf"),
        ("day1_high_kis", "day1_high_yf"),
        ("day1_close_kis", "day1_close_yf"),
    ]

    results = []

    for kis_field, yf_field in fields_to_compare:
        print(f"Comparing {kis_field} (KIS) vs {yf_field} (yfinance)...")
        print("-" * 80)

        matches = 0
        mismatches = 0
        kis_missing = 0
        yf_missing = 0
        both_missing = 0

        mismatch_details = []

        for idx, row in df.iterrows():
            company_name = row["company_name"]
            code = row["code"]
            kis_val = row.get(kis_field)
            yf_val = row.get(yf_field)

            comparison = compare_values(kis_val, yf_val, kis_field)

            if comparison["status"] == "match":
                matches += 1
            elif comparison["status"] == "mismatch":
                mismatches += 1
                mismatch_details.append({
                    "company": company_name,
                    "code": code,
                    "field": kis_field,
                    "kis_val": comparison["kis_val"],
                    "yf_val": comparison["yf_val"],
                    "diff": comparison["diff"],
                    "rel_diff_pct": comparison["rel_diff_pct"],
                })
            elif comparison["status"] == "kis_missing":
                kis_missing += 1
            elif comparison["status"] == "yf_missing":
                yf_missing += 1
            elif comparison["status"] == "both_missing":
                both_missing += 1

        total = matches + mismatches + kis_missing + yf_missing + both_missing

        print(f"  Total: {total}")
        print(f"  ✓ Matches: {matches} ({matches/total*100:.1f}%)")
        print(f"  ✗ Mismatches: {mismatches} ({mismatches/total*100:.1f}%)")
        print(f"  - KIS missing: {kis_missing}")
        print(f"  - yfinance missing: {yf_missing}")
        print(f"  - Both missing: {both_missing}")
        print()

        if mismatch_details:
            print(f"  Top 10 mismatches:")
            for detail in mismatch_details[:10]:
                print(
                    f"    {detail['company']} ({detail['code']}): "
                    f"KIS={detail['kis_val']:.0f}원, yfinance={detail['yf_val']:.0f}원, "
                    f"diff={detail['rel_diff_pct']:.2f}%"
                )
            print()

        results.append({
            "field": kis_field,
            "total": total,
            "matches": matches,
            "mismatches": mismatches,
            "kis_missing": kis_missing,
            "yf_missing": yf_missing,
            "both_missing": both_missing,
            "match_rate": matches / total * 100 if total > 0 else 0,
        })

    return results


def validate_2025_data():
    """Validate 2025 IPO data"""
    print("=" * 80)
    print("VALIDATING 2025 IPO DATA (KIS vs yfinance)")
    print("=" * 80)
    print()

    # Load yfinance dataset (contains both KIS and yfinance data)
    df = pd.read_csv("data/raw/ipo_2025_dataset_yfinance.csv")

    print(f"Dataset: {len(df)} IPOs")
    print()

    # Fields to compare
    fields_to_compare = [
        ("day0_open", "day0_open_yf"),
        ("day0_high", "day0_high_yf"),
        ("day0_low", "day0_low_yf"),
        ("day0_close", "day0_close_yf"),
        ("day0_volume", "day0_volume_yf"),
        ("day1_open", "day1_open_yf"),
        ("day1_high", "day1_high_yf"),
        ("day1_low", "day1_low_yf"),
        ("day1_close", "day1_close_yf"),
        ("day1_volume", "day1_volume_yf"),
    ]

    results = []

    for kis_field, yf_field in fields_to_compare:
        print(f"Comparing {kis_field} (KIS) vs {yf_field} (yfinance)...")
        print("-" * 80)

        matches = 0
        mismatches = 0
        kis_missing = 0
        yf_missing = 0
        both_missing = 0

        mismatch_details = []

        for idx, row in df.iterrows():
            company_name = row["company_name"]
            code = row["code"]
            kis_val = row.get(kis_field)
            yf_val = row.get(yf_field)

            comparison = compare_values(kis_val, yf_val, kis_field)

            if comparison["status"] == "match":
                matches += 1
            elif comparison["status"] == "mismatch":
                mismatches += 1
                mismatch_details.append({
                    "company": company_name,
                    "code": code,
                    "field": kis_field,
                    "kis_val": comparison["kis_val"],
                    "yf_val": comparison["yf_val"],
                    "diff": comparison["diff"],
                    "rel_diff_pct": comparison["rel_diff_pct"],
                })
            elif comparison["status"] == "kis_missing":
                kis_missing += 1
            elif comparison["status"] == "yf_missing":
                yf_missing += 1
            elif comparison["status"] == "both_missing":
                both_missing += 1

        total = matches + mismatches + kis_missing + yf_missing + both_missing

        print(f"  Total: {total}")
        print(f"  ✓ Matches: {matches} ({matches/total*100:.1f}%)")
        print(f"  ✗ Mismatches: {mismatches} ({mismatches/total*100:.1f}%)")
        print(f"  - KIS missing: {kis_missing}")
        print(f"  - yfinance missing: {yf_missing}")
        print(f"  - Both missing: {both_missing}")
        print()

        if mismatch_details:
            print(f"  Top 5 mismatches:")
            for detail in mismatch_details[:5]:
                print(
                    f"    {detail['company']} ({detail['code']}): "
                    f"KIS={detail['kis_val']:.0f}, yfinance={detail['yf_val']:.0f}, "
                    f"diff={detail['rel_diff_pct']:.2f}%"
                )
            print()

        results.append({
            "field": kis_field,
            "total": total,
            "matches": matches,
            "mismatches": mismatches,
            "kis_missing": kis_missing,
            "yf_missing": yf_missing,
            "both_missing": both_missing,
            "match_rate": matches / total * 100 if total > 0 else 0,
        })

    return results


def main():
    print()
    print("IPO OHLCV DATA VALIDATION")
    print("Comparing KIS API data vs yfinance data")
    print()

    # Validate 2022-2024 data
    results_2022_2024 = validate_2022_2024_data()

    # Validate 2025 data
    results_2025 = validate_2025_data()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()

    print("2022-2024 Data:")
    print("-" * 80)
    for result in results_2022_2024:
        print(
            f"  {result['field']:15s}: "
            f"{result['matches']}/{result['total']} matches ({result['match_rate']:.1f}%), "
            f"{result['mismatches']} mismatches"
        )
    print()

    print("2025 Data:")
    print("-" * 80)
    for result in results_2025:
        print(
            f"  {result['field']:15s}: "
            f"{result['matches']}/{result['total']} matches ({result['match_rate']:.1f}%), "
            f"{result['mismatches']} mismatches"
        )
    print()

    print("✅ Validation complete")


if __name__ == "__main__":
    main()
