"""
Demo script for GBM forecasting API.

This script calls the forecast endpoint and creates visualizations.

Usage:
    python demo_forecast.py
"""

import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# API endpoint
API_BASE = "http://localhost:8000/api"


def forecast_and_plot(symbol="SPY", horizon_days=30, n_paths=50000):
    """
    Fetch forecast and create visualizations.
    
    Args:
        symbol: Stock symbol
        horizon_days: Forecast horizon
        n_paths: Number of Monte Carlo paths
    """
    print(f"\n{'='*60}")
    print(f"Forecasting {symbol} - {horizon_days} days ahead")
    print(f"{'='*60}\n")
    
    # Make API request
    print(f"Calling API with {n_paths:,} paths...")
    response = requests.post(
        f"{API_BASE}/forecast/gbm",
        json={
            "symbol": symbol,
            "horizon_days": horizon_days,
            "n_paths": n_paths,
            "calibration_days": 252,
            "include_paths": True,
            "n_sample_paths": 200  # Get 200 sample paths for plotting
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print("✓ Forecast complete!\n")
    
    # Print summary statistics
    print(f"Current Price: ${data['current_price']:.2f}")
    print(f"\nForecast ({horizon_days} days):")
    print(f"  Mean:   ${data['mean']:.2f}")
    print(f"  Median: ${data['median']:.2f}")
    print(f"  Std:    ${data['std']:.2f}")
    print(f"\nConfidence Intervals:")
    print(f"  95% CI: ${data['percentiles']['p05']:.2f} - ${data['percentiles']['p95']:.2f}")
    print(f"  50% CI: ${data['percentiles']['p25']:.2f} - ${data['percentiles']['p75']:.2f}")
    print(f"\nRisk Metrics:")
    print(f"  VaR (95%):  ${data['var_95']:.2f}")
    print(f"  CVaR (95%): ${data['cvar_95']:.2f}")
    print(f"  P(gain):    {data['probability_above_current']*100:.1f}%")
    print(f"  E(return):  {data['expected_return']*100:.2f}%")
    print(f"\nModel Parameters:")
    print(f"  μ (drift):      {data['parameters']['mu']:.4f} ({data['parameters']['interpretation']['annual_return']})")
    print(f"  σ (volatility): {data['parameters']['sigma']:.4f} ({data['parameters']['interpretation']['annual_volatility']})")
    
    # Create visualizations
    print(f"\nCreating plots...")
    create_plots(data, symbol, horizon_days)
    print("✓ Plots saved!\n")


def create_plots(data, symbol, horizon_days):
    """Create comprehensive forecast visualizations."""
    
    fig = plt.figure(figsize=(16, 10))
    
    # Plot 1: Sample paths (top left)
    ax1 = plt.subplot(2, 2, 1)
    sample_paths = np.array(data['sample_paths'])
    days = np.arange(horizon_days + 1)
    
    # Plot sample paths
    for path in sample_paths[:100]:  # Plot first 100 paths
        ax1.plot(days, path, alpha=0.1, color='steelblue', linewidth=0.5)
    
    # Plot mean path
    mean_path = np.mean(sample_paths, axis=0)
    ax1.plot(days, mean_path, color='darkblue', linewidth=2, label='Mean forecast')
    
    # Plot current price
    ax1.axhline(data['current_price'], color='black', linestyle='--', linewidth=2, label='Current price')
    
    # Confidence bands
    p05_path = np.percentile(sample_paths, 5, axis=0)
    p95_path = np.percentile(sample_paths, 95, axis=0)
    ax1.fill_between(days, p05_path, p95_path, alpha=0.2, color='green', label='95% confidence')
    
    ax1.set_xlabel('Days')
    ax1.set_ylabel('Price ($)')
    ax1.set_title(f'{symbol} Price Forecast - Sample Paths', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Distribution histogram (top right)
    ax2 = plt.subplot(2, 2, 2)
    terminal_prices = sample_paths[:, -1]  # Last column = terminal prices
    
    ax2.hist(terminal_prices, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax2.axvline(data['current_price'], color='black', linestyle='--', linewidth=2, label='Current')
    ax2.axvline(data['mean'], color='darkblue', linestyle='-', linewidth=2, label='Mean')
    ax2.axvline(data['median'], color='green', linestyle='-', linewidth=2, label='Median')
    ax2.axvline(data['percentiles']['p05'], color='red', linestyle=':', linewidth=2, label='5th percentile')
    ax2.axvline(data['percentiles']['p95'], color='red', linestyle=':', linewidth=2, label='95th percentile')
    
    ax2.set_xlabel('Terminal Price ($)')
    ax2.set_ylabel('Frequency')
    ax2.set_title(f'Distribution of Outcomes ({horizon_days} days)', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Confidence intervals (bottom left)
    ax3 = plt.subplot(2, 2, 3)
    percentiles = [5, 25, 50, 75, 95]
    percentile_values = [
        data['percentiles']['p05'],
        data['percentiles']['p25'],
        data['percentiles']['p50'],
        data['percentiles']['p75'],
        data['percentiles']['p95']
    ]
    
    colors = ['red', 'orange', 'green', 'orange', 'red']
    bars = ax3.barh(percentiles, percentile_values, color=colors, alpha=0.7, edgecolor='black')
    ax3.axvline(data['current_price'], color='black', linestyle='--', linewidth=2, label='Current')
    
    # Add value labels
    for i, (p, v) in enumerate(zip(percentiles, percentile_values)):
        ax3.text(v, p, f' ${v:.2f}', va='center', fontweight='bold')
    
    ax3.set_xlabel('Price ($)')
    ax3.set_ylabel('Percentile')
    ax3.set_title('Confidence Intervals', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='x')
    
    # Plot 4: Risk metrics (bottom right)
    ax4 = plt.subplot(2, 2, 4)
    ax4.axis('off')
    
    # Create summary text
    summary_text = f"""
    {symbol} FORECAST SUMMARY
    {'='*40}
    
    Current Price:     ${data['current_price']:.2f}
    
    FORECAST ({horizon_days} days ahead):
    Mean:              ${data['mean']:.2f}
    Median:            ${data['median']:.2f}
    Std Dev:           ${data['std']:.2f}
    
    CONFIDENCE INTERVALS:
    95% CI:  ${data['percentiles']['p05']:.2f} - ${data['percentiles']['p95']:.2f}
    50% CI:  ${data['percentiles']['p25']:.2f} - ${data['percentiles']['p75']:.2f}
    
    RISK METRICS:
    VaR (95%):         ${data['var_95']:.2f}
    CVaR (95%):        ${data['cvar_95']:.2f}
    Prob. of Gain:     {data['probability_above_current']*100:.1f}%
    Expected Return:   {data['expected_return']*100:.2f}%
    
    MODEL PARAMETERS:
    Annual Return:     {data['parameters']['interpretation']['annual_return']}
    Annual Volatility: {data['parameters']['interpretation']['annual_volatility']}
    
    CALIBRATION:
    Period: {data['calibration_period']['days']} days
    From:   {data['calibration_period']['start'][:10]}
    To:     {data['calibration_period']['end'][:10]}
    """
    
    ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save figure
    filename = f"{symbol}_forecast_{horizon_days}d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"  Saved: {filename}")
    
    # Show plot
    plt.show()


def compare_horizons(symbol="SPY", horizons=[7, 30, 90]):
    """Compare forecasts at different time horizons."""
    print(f"\n{'='*60}")
    print(f"Comparing Time Horizons for {symbol}")
    print(f"{'='*60}\n")
    
    fig, axes = plt.subplots(1, len(horizons), figsize=(16, 5))
    
    for idx, days in enumerate(horizons):
        print(f"Fetching {days}-day forecast...")
        
        response = requests.post(
            f"{API_BASE}/forecast/gbm",
            json={
                "symbol": symbol,
                "horizon_days": days,
                "n_paths": 20000,
                "calibration_days": 252,
                "include_paths": True,
                "n_sample_paths": 100
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Error for {days} days")
            continue
        
        data = response.json()
        sample_paths = np.array(data['sample_paths'])
        
        ax = axes[idx]
        
        # Plot sample paths
        for path in sample_paths[:50]:
            ax.plot(path, alpha=0.1, color='steelblue', linewidth=0.5)
        
        # Mean and confidence
        mean_path = np.mean(sample_paths, axis=0)
        p05_path = np.percentile(sample_paths, 5, axis=0)
        p95_path = np.percentile(sample_paths, 95, axis=0)
        
        ax.plot(mean_path, color='darkblue', linewidth=2, label='Mean')
        ax.fill_between(range(len(mean_path)), p05_path, p95_path, 
                        alpha=0.2, color='green', label='95% CI')
        ax.axhline(data['current_price'], color='black', linestyle='--', 
                  linewidth=2, label='Current')
        
        ax.set_title(f'{days}-Day Forecast\nσ=${data["std"]:.2f}', 
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('Days')
        if idx == 0:
            ax.set_ylabel('Price ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.suptitle(f'{symbol} Forecast Comparison', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    filename = f"{symbol}_horizon_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n✓ Saved: {filename}")
    plt.show()


if __name__ == "__main__":
    # Demo 1: Single forecast with comprehensive plots
    forecast_and_plot("VUSA.L", horizon_days=30, n_paths=50000)
    
    # Demo 2: Compare different time horizons
    compare_horizons("VUSA.L", horizons=[7, 30, 90])
    
    # Demo 3: Try different stocks
    # forecast_and_plot("MSFT", horizon_days=60, n_paths=30000)
    # forecast_and_plot("BTC", horizon_days=14, n_paths=50000)