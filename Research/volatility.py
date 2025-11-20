import numpy as np
import matplotlib.pyplot as plt

# Parameters
mu = 0.1       # annual drift (10%)
sigma = 0.2    # annual volatility (20%)
S0 = 100
T = 10.0        # 1 year
N = 2520        # daily steps
dt = T / N


# Generate Brownian motion
#np.random.seed(42)
Z = np.random.normal(0, 1, N)
W = np.cumsum(np.sqrt(dt) * Z)
t = np.linspace(0, T, N)

# Case A: Drift only
S_drift = S0 * np.exp(mu * t)
# Case B: Volatility only
S_vol = S0 * np.exp(-0.5 * sigma**2 * t + sigma * W)
# Case C: Full GBM
S_full = S0 * np.exp((mu - 0.5 * sigma**2) * t + sigma * W)

# Plot 1: Price space
plt.figure(figsize=(10, 10))

plt.subplot(2, 1, 1)
plt.plot(t, S_drift, label='Drift only (μ S_t dt)', color='orange', linewidth=2)
plt.plot(t, S_vol, label='Volatility only (σ S_t dW_t)', color='gray', linestyle='--')
plt.plot(t, S_full, label='Full GBM', color='blue')
plt.title('GBM Components in Price Space')
plt.ylabel('Price')
plt.legend()
plt.grid(True)

# Plot 2: Log-price space
plt.subplot(2, 1, 2)
plt.plot(t, np.log(S_drift / S0), color='orange', linewidth=2)
plt.plot(t, np.log(S_vol / S0), color='gray', linestyle='--')
plt.plot(t, np.log(S_full / S0), color='blue')
plt.title('GBM Components in Log-Price Space')
plt.xlabel('Time (years)')
plt.ylabel('log(S_t / S_0)')
plt.grid(True)

plt.tight_layout()
plt.show()