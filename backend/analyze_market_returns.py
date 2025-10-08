"""Analyze IPO returns by listing market (KOSDAQ vs KOSPI)"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Load enhanced dataset
df = pd.read_csv("data/raw/ipo_full_dataset_2022_2024_enhanced.csv")

print("="*80)
print("KOSDAQ vs KOSPI RETURN ANALYSIS")
print("="*80)
print(f"\nTotal IPOs: {len(df)}")
print(f"Date range: {df['listing_date'].min()} to {df['listing_date'].max()}")

# Count by market
market_counts = df['listing_method'].value_counts()
print(f"\nMarket Distribution:")
for market, count in market_counts.items():
    print(f"  {market}: {count} ({count/len(df)*100:.1f}%)")

# Calculate returns
df['day0_high_return'] = ((df['day0_high'] - df['ipo_price_confirmed']) / df['ipo_price_confirmed'] * 100)
df['day0_close_return'] = ((df['day0_close'] - df['ipo_price_confirmed']) / df['ipo_price_confirmed'] * 100)
df['day1_close_return'] = ((df['day1_close'] - df['ipo_price_confirmed']) / df['ipo_price_confirmed'] * 100)

print("\n" + "="*80)
print("RETURN STATISTICS BY MARKET")
print("="*80)

for market in sorted(df['listing_method'].unique()):
    df_market = df[df['listing_method'] == market]

    print(f"\n{market} (n={len(df_market)})")
    print("-"*80)

    for return_col in ['day0_high_return', 'day0_close_return', 'day1_close_return']:
        returns = df_market[return_col].dropna()

        target_name = return_col.replace('_return', '').replace('_', ' ').title()

        print(f"\n  {target_name}:")
        print(f"    Mean:     {returns.mean():>8.2f}%")
        print(f"    Median:   {returns.median():>8.2f}%")
        print(f"    Std Dev:  {returns.std():>8.2f}%")
        print(f"    Min:      {returns.min():>8.2f}%")
        print(f"    Max:      {returns.max():>8.2f}%")
        print(f"    Positive: {(returns > 0).sum()}/{len(returns)} ({(returns > 0).sum()/len(returns)*100:.1f}%)")

# Statistical tests
print("\n" + "="*80)
print("STATISTICAL SIGNIFICANCE TESTS (KOSDAQ vs KOSPI)")
print("="*80)

kosdaq_data = df[df['listing_method'] == 'KOSDAQ']
kospi_data = df[df['listing_method'] == 'KOSPI']

for return_col in ['day0_high_return', 'day0_close_return', 'day1_close_return']:
    kosdaq_returns = kosdaq_data[return_col].dropna()
    kospi_returns = kospi_data[return_col].dropna()

    target_name = return_col.replace('_return', '').replace('_', ' ').title()

    # T-test
    t_stat, t_pval = stats.ttest_ind(kosdaq_returns, kospi_returns)

    # Mann-Whitney U test (non-parametric)
    u_stat, u_pval = stats.mannwhitneyu(kosdaq_returns, kospi_returns, alternative='two-sided')

    print(f"\n{target_name}:")
    print(f"  KOSDAQ mean: {kosdaq_returns.mean():.2f}%")
    print(f"  KOSPI mean:  {kospi_returns.mean():.2f}%")
    print(f"  Difference:  {kosdaq_returns.mean() - kospi_returns.mean():.2f}%")
    print(f"  ")
    print(f"  T-test:")
    print(f"    t-statistic: {t_stat:.4f}")
    print(f"    p-value:     {t_pval:.4f} {'***' if t_pval < 0.001 else '**' if t_pval < 0.01 else '*' if t_pval < 0.05 else 'ns'}")
    print(f"  ")
    print(f"  Mann-Whitney U test:")
    print(f"    U-statistic: {u_stat:.0f}")
    print(f"    p-value:     {u_pval:.4f} {'***' if u_pval < 0.001 else '**' if u_pval < 0.01 else '*' if u_pval < 0.05 else 'ns'}")

print("\n" + "="*80)
print("INTERPRETATION")
print("="*80)
print("Significance levels:")
print("  *** p < 0.001 (highly significant)")
print("  **  p < 0.01  (very significant)")
print("  *   p < 0.05  (significant)")
print("  ns  p >= 0.05 (not significant)")

# Create visualization
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, return_col in enumerate(['day0_high_return', 'day0_close_return', 'day1_close_return']):
    ax = axes[idx]

    # Prepare data for boxplot
    kosdaq_returns = df[df['listing_method'] == 'KOSDAQ'][return_col].dropna()
    kospi_returns = df[df['listing_method'] == 'KOSPI'][return_col].dropna()

    data_to_plot = [kosdaq_returns, kospi_returns]

    bp = ax.boxplot(data_to_plot, labels=['KOSDAQ', 'KOSPI'], patch_artist=True)

    # Color boxes
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    target_name = return_col.replace('_return', '').replace('_', ' ').title()
    ax.set_title(target_name, fontsize=12, fontweight='bold')
    ax.set_ylabel('Return (%)', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)

plt.tight_layout()
plt.savefig('/tmp/kosdaq_vs_kospi_returns.png', dpi=150, bbox_inches='tight')
print("\n✅ Saved visualization to: /tmp/kosdaq_vs_kospi_returns.png")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
