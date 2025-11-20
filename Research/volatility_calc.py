import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# --- Simulation setup ---
np.random.seed(42)
T = 1.0          # 1 year
N = 252          # trading days
dt = T / N
t = np.linspace(0, T, N)
S0 = 100
mu = 0.05
sigma_true = 0.2   # "true" instantaneous volatility

# --- 1. Simulate a GBM price path ---
Z = np.random.randn(N)
S = np.zeros(N)
S[0] = S0
for i in range(1, N):
    S[i] = S[i-1] * np.exp((mu - 0.5 * sigma_true**2) * dt + sigma_true * np.sqrt(dt) * Z[i])

# --- 2. Compute HISTORICAL volatility from returns ---
returns = np.diff(np.log(S))
sigma_hist_daily = np.std(returns)
sigma_hist_annual = sigma_hist_daily * np.sqrt(252)

# --- 3. Compute REALIZED volatility (using true sigma) ---
sigma_realized = sigma_true  # since we simulated constant σ
# (If σₜ varied, we would take sqrt((1/T) ∫ σₜ² dt))

# --- 4. Compute IMPLIED volatility from a synthetic option price ---
def black_scholes_call(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r*T) * norm.cdf(d2)

# Suppose we observe a call option price in the market:
K = 100
r = 0.02
true_price = black_scholes_call(S0, K, T, r, sigma_true)

# We'll "invert" the model to find the implied volatility:
def implied_vol_call(S, K, T, r, market_price, tol=1e-6, max_iter=100):
    sigma = 0.3  # initial guess
    for _ in range(max_iter):
        price = black_scholes_call(S, K, T, r, sigma)
        vega = S * norm.pdf((np.log(S/K)+(r+0.5*sigma**2)*T)/(sigma*np.sqrt(T))) * np.sqrt(T)
        diff = market_price - price
        if abs(diff) < tol:
            break
        sigma += diff / vega  # Newton-Raphson update
    return sigma

sigma_implied = implied_vol_call(S0, K, T, r, true_price)

# --- Print comparison ---
print(f"True volatility:       {sigma_true:.4f}")
print(f"Historical volatility: {sigma_hist_annual:.4f}")
print(f"Implied volatility:    {sigma_implied:.4f}")

# --- Plot ---
plt.figure(figsize=(10,5))
plt.plot(t, S, lw=2)
plt.title("Simulated Price Path (GBM)")
plt.xlabel("Time (years)")
plt.ylabel("Price")
plt.show()