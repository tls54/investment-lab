import numpy as np
import matplotlib.pyplot as plt

# Simulation parameters
np.random.seed(42)
T = 1.0          # total time (1 year)
N = 252          # trading days
dt = T / N
t = np.linspace(0, T, N)
n_paths = 5     # number of simulated paths

# --- GBM parameters ---
S0 = 100
mu = 0.05
sigma = 0.2

# --- Heston parameters ---
v0 = sigma**2
kappa = 2.0      # mean reversion speed
theta = sigma**2 # long-term variance
xi = 0.3         # vol of vol
rho = -0.7       # correlation between price & vol

# --- Storage arrays ---
S_gbm = np.zeros((n_paths, N))
S_heston = np.zeros((n_paths, N))
v = np.zeros((n_paths, N))

S_gbm[:, 0] = S0
S_heston[:, 0] = S0
v[:, 0] = v0

# --- Simulate paths ---
for j in range(n_paths):
    Z1 = np.random.randn(N)
    Z2 = rho * Z1 + np.sqrt(1 - rho**2) * np.random.randn(N)
    for i in range(1, N):
        # GBM
        S_gbm[j, i] = S_gbm[j, i-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z1[i])
        # Heston variance (CIR process)
        v[j, i] = np.abs(v[j, i-1] + kappa * (theta - v[j, i-1]) * dt + xi * np.sqrt(v[j, i-1] * dt) * Z2[i])
        # Heston price
        S_heston[j, i] = S_heston[j, i-1] * np.exp((mu - 0.5 * v[j, i]) * dt + np.sqrt(v[j, i] * dt) * Z1[i])

# --- Plot results ---
fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# GBM paths
for j in range(n_paths):
    ax[0].plot(t, S_gbm[j], lw=1)
ax[0].set_title("GBM (constant volatility)")
ax[0].set_ylabel("Price")

# Heston paths
for j in range(n_paths):
    ax[1].plot(t, S_heston[j], lw=1)
ax[1].set_title("Heston (stochastic volatility)")
ax[1].set_xlabel("Time")
ax[1].set_ylabel("Price")

plt.suptitle("Comparison of GBM vs Heston Model (20 simulated paths)", fontsize=14)
plt.tight_layout()
plt.show()