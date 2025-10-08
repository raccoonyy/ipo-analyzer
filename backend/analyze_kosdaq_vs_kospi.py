"""Analyze KOSDAQ vs KOSPI returns using combined dataset"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

print("="*80)
print("KOSDAQ vs KOSPI RETURN ANALYSIS")
print("="*80)
print()

# Load KOSPI data from yfinance
df_kospi = pd.read_csv('data/raw/kospi_ipo_yfinance.csv')
df_kospi['listing_method'] = 'KOSPI'

# Load KOSDAQ data (enhanced dataset with KIS API data)
df_kosdaq = pd.read_csv('data/raw/ipo_full_dataset_2022_2024_enhanced.csv')

# Add 38.co.kr subscription data for missing fields
df_sub = pd.read_csv('data/raw/38_subscription_data.csv')

# Merge KOSDAQ with subscription data to get ipo_price
df_kosdaq = df_kosdaq.merge(
    df_sub[['code', 'ipo_price']],
    left_on='code',
    right_on='code',
    how='left',
    suffixes=('', '_38')
)

# Use ipo_price_confirmed if available, otherwise use ipo_price from 38
df_kosdaq['ipo_price_final'] = df_kosdaq['ipo_price_confirmed'].fillna(df_kosdaq['ipo_price'])

# For KOSPI, we need IPO price from 38
df_kospi = df_kospi.merge(
    df_sub[['code', 'ipo_price']],
    left_on='code',
    right_on='code',
    how='left'
)

print(f"KOSDAQ IPOs: {len(df_kosdaq)}")
print(f"KOSPI IPOs: {len(df_kospi)}")
print()

# Calculate returns for KOSDAQ
df_kosdaq['day0_high_return'] = ((df_kosdaq['day0_high'] - df_kosdaq['ipo_price_final']) / df_kosdaq['ipo_price_final'] * 100)
df_kosdaq['day0_close_return'] = ((df_kosdaq['day0_close'] - df_kosdaq['ipo_price_final']) / df_kosdaq['ipo_price_final'] * 100)
df_kosdaq['day1_close_return'] = ((df_kosdaq['day1_close'] - df_kosdaq['ipo_price_final']) / df_kosdaq['ipo_price_final'] * 100)

# Calculate returns for KOSPI
df_kospi['day0_high_return'] = ((df_kospi['day0_high'] - df_kospi['ipo_price']) / df_kospi['ipo_price'] * 100)
df_kospi['day0_close_return'] = ((df_kospi['day0_close'] - df_kospi['ipo_price']) / df_kospi['ipo_price'] * 100)
df_kospi['day1_close_return'] = ((df_kospi['day1_close'] - df_kospi['ipo_price']) / df_kospi['ipo_price'] * 100)

# Combine
df_combined = pd.concat([
    df_kosdaq[['company_name', 'listing_date', 'listing_method', 'day0_high_return', 'day0_close_return', 'day1_close_return']],
    df_kospi[['company_name', 'listing_date', 'listing_method', 'day0_high_return', 'day0_close_return', 'day1_close_return']]
], ignore_index=True)

print("="*80)
print("RETURN STATISTICS BY MARKET")
print("="*80)

for market in ['KOSDAQ', 'KOSPI']:
    df_market = df_combined[df_combined['listing_method'] == market]

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
print("STATISTICAL SIGNIFICANCE TESTS")
print("="*80)

kosdaq_data = df_combined[df_combined['listing_method'] == 'KOSDAQ']
kospi_data = df_combined[df_combined['listing_method'] == 'KOSPI']

for return_col in ['day0_high_return', 'day0_close_return', 'day1_close_return']:
    kosdaq_returns = kosdaq_data[return_col].dropna()
    kospi_returns = kospi_data[return_col].dropna()

    target_name = return_col.replace('_return', '').replace('_', ' ').title()

    # T-test
    t_stat, t_pval = stats.ttest_ind(kosdaq_returns, kospi_returns)

    # Mann-Whitney U test
    u_stat, u_pval = stats.mannwhitneyu(kosdaq_returns, kospi_returns, alternative='two-sided')

    print(f"\n{target_name}:")
    print(f"  KOSDAQ mean: {kosdaq_returns.mean():>8.2f}%  (n={len(kosdaq_returns)})")
    print(f"  KOSPI mean:  {kospi_returns.mean():>8.2f}%  (n={len(kospi_returns)})")
    print(f"  Difference:  {kosdaq_returns.mean() - kospi_returns.mean():>8.2f}%")
    print(f"  ")
    print(f"  T-test p-value:     {t_pval:.4f} {'***' if t_pval < 0.001 else '**' if t_pval < 0.01 else '*' if t_pval < 0.05 else 'ns'}")
    print(f"  Mann-Whitney U p-value: {u_pval:.4f} {'***' if u_pval < 0.001 else '**' if u_pval < 0.01 else '*' if u_pval < 0.05 else 'ns'}")

# Visualization
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, return_col in enumerate(['day0_high_return', 'day0_close_return', 'day1_close_return']):
    ax = axes[idx]

    kosdaq_returns = df_combined[df_combined['listing_method'] == 'KOSDAQ'][return_col].dropna()
    kospi_returns = df_combined[df_combined['listing_method'] == 'KOSPI'][return_col].dropna()

    data_to_plot = [kosdaq_returns, kospi_returns]

    bp = ax.boxplot(data_to_plot, tick_labels=['KOSDAQ', 'KOSPI'], patch_artist=True)

    # Color boxes
    colors = ['lightblue', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)

    target_name = return_col.replace('_return', '').replace('_', ' ').title()
    ax.set_title(f'{target_name}\nKOSDAQ (n={len(kosdaq_returns)}) vs KOSPI (n={len(kospi_returns)})',
                 fontsize=11, fontweight='bold')
    ax.set_ylabel('Return (%)', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)

    # Add mean markers
    means = [kosdaq_returns.mean(), kospi_returns.mean()]
    ax.plot([1, 2], means, 'D', color='red', markersize=8, label='Mean', zorder=3)

plt.tight_layout()
plt.savefig('/tmp/kosdaq_vs_kospi_returns_final.png', dpi=150, bbox_inches='tight')

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print(f"\n✅ Analysis complete!")
print(f"   - KOSDAQ IPOs: {len(kosdaq_data)}")
print(f"   - KOSPI IPOs: {len(kospi_data)}")
print(f"   - Visualization saved to: /tmp/kosdaq_vs_kospi_returns_final.png")
print()
