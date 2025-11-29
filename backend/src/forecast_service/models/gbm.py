"""
Geometric Brownian Motion (GBM) model for price forecasting.

GBM assumes:
- Log returns are normally distributed
- Constant drift (μ) and volatility (σ)
- No jumps or regime changes

Good for: Short-term forecasts (days to weeks), stable markets
Not good for: Long-term (>6 months), volatile events, regime changes
"""

import numpy as np
import torch
from dataclasses import dataclass
from typing import Optional, List, Dict
import logging

from ..device_utils import select_device

logger = logging.getLogger(__name__)


@dataclass
class GBMParams:
    """
    Parameters for Geometric Brownian Motion.
    
    Attributes:
        mu: Drift (expected return, annualized)
        sigma: Volatility (standard deviation, annualized)
        S0: Initial price
    """
    mu: float
    sigma: float
    S0: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "mu": self.mu,
            "sigma": self.sigma,
            "S0": self.S0,
            "interpretation": {
                "annual_return": f"{self.mu * 100:.2f}%",
                "annual_volatility": f"{self.sigma * 100:.2f}%",
                "initial_price": f"${self.S0:.2f}"
            }
        }


class GBMModel:
    """
    Geometric Brownian Motion model for price forecasting.
    
    Uses PyTorch for GPU acceleration when available.
    
    Example:
        # Create model
        model = GBMModel(use_gpu=True)
        
        # Calibrate from historical data
        prices = [100, 102, 101, 103, ...]
        params = model.calibrate(prices)
        
        # Forecast 30 days ahead
        result = model.forecast(
            params=params,
            horizon_days=30,
            n_paths=10000
        )
        
        print(f"Expected price: ${result['mean']:.2f}")
        print(f"95% confidence: ${result['p05']:.2f} - ${result['p95']:.2f}")
    """
    
    def __init__(self, use_gpu: bool = True):
        """
        Initialize GBM model.

        Args:
            use_gpu: Use GPU if available (default: True)
                Supports CUDA (NVIDIA), MPS (Apple Silicon), or CPU fallback
        """
        self.device = select_device(use_gpu=use_gpu, verbose=True)
    
    def calibrate(
        self,
        prices: np.ndarray,
        trading_days_per_year: int = 252
    ) -> GBMParams:
        """
        Calibrate GBM parameters from historical prices using MLE.
        
        Maximum Likelihood Estimation assumes log returns are normal.
        
        Args:
            prices: Array of historical prices (oldest first)
            trading_days_per_year: For annualization (default: 252)
            
        Returns:
            Calibrated GBM parameters
            
        Raises:
            ValueError: If insufficient data (need at least 2 prices)
        """
        if len(prices) < 2:
            raise ValueError("Need at least 2 prices for calibration")
        
        # Convert to numpy array if needed
        prices = np.asarray(prices)
        
        # Calculate log returns
        log_returns = np.diff(np.log(prices))
        
        # Time step (assuming daily data)
        dt = 1 / trading_days_per_year
        
        # MLE estimates
        # μ = E[log return] / dt + σ²/2
        # σ = std[log return] / sqrt(dt)
        mean_log_return = np.mean(log_returns)
        std_log_return = np.std(log_returns, ddof=1)  # Sample std
        
        # Annualized parameters
        mu = mean_log_return / dt + 0.5 * (std_log_return / np.sqrt(dt)) ** 2
        sigma = std_log_return / np.sqrt(dt)
        
        # Current price (last observation)
        S0 = float(prices[-1])
        
        params = GBMParams(mu=mu, sigma=sigma, S0=S0)
        
        logger.info(
            f"Calibrated GBM: μ={mu:.4f} ({mu*100:.2f}%), "
            f"σ={sigma:.4f} ({sigma*100:.2f}%), S0={S0:.2f}"
        )
        
        return params
    
    def simulate(
        self,
        params: GBMParams,
        horizon_days: int,
        n_paths: int = 10000,
        n_steps: Optional[int] = None,
        return_paths: bool = False
    ) -> torch.Tensor:
        """
        Simulate GBM paths using GPU-accelerated Monte Carlo.
        
        This is the core simulation engine. It generates many possible
        future price paths based on the GBM assumptions.
        
        Args:
            params: Calibrated GBM parameters
            horizon_days: Forecast horizon in days
            n_paths: Number of Monte Carlo paths
            n_steps: Number of time steps (default: same as horizon_days)
            return_paths: If True, return full paths; else just terminal values
            
        Returns:
            Tensor of shape (n_paths,) or (n_paths, n_steps+1) depending on return_paths
        """
        if n_steps is None:
            n_steps = horizon_days
        
        # Time step
        T = horizon_days / 252  # Convert to years
        dt = T / n_steps
        
        # Move to GPU
        S0_tensor = torch.tensor(params.S0, device=self.device, dtype=torch.float32)
        mu_tensor = torch.tensor(params.mu, device=self.device, dtype=torch.float32)
        sigma_tensor = torch.tensor(params.sigma, device=self.device, dtype=torch.float32)
        
        if return_paths:
            # Store full paths
            paths = torch.zeros(n_paths, n_steps + 1, device=self.device)
            paths[:, 0] = S0_tensor
            
            # Generate random numbers for all steps
            Z = torch.randn(n_paths, n_steps, device=self.device)
            
            # GBM discrete formula: S_{t+1} = S_t * exp((μ - σ²/2)dt + σ√dt * Z)
            drift = (mu_tensor - 0.5 * sigma_tensor ** 2) * dt
            diffusion = sigma_tensor * np.sqrt(dt)
            
            # Vectorized path generation
            for t in range(n_steps):
                paths[:, t + 1] = paths[:, t] * torch.exp(drift + diffusion * Z[:, t])
            
            return paths
        
        else:
            # Only compute terminal values (more memory efficient)
            # Generate all random numbers at once
            Z = torch.randn(n_paths, n_steps, device=self.device)
            
            # Sum of Z gives the total random shock
            total_shock = Z.sum(dim=1)
            
            # Terminal value formula
            drift = (mu_tensor - 0.5 * sigma_tensor ** 2) * T
            diffusion = sigma_tensor * np.sqrt(dt) * total_shock
            
            terminal_prices = S0_tensor * torch.exp(drift + diffusion)
            
            return terminal_prices
    
    def forecast(
        self,
        params: GBMParams,
        horizon_days: int,
        n_paths: int = 10000,
        percentiles: Optional[List[float]] = None
    ) -> Dict:
        """
        Generate forecast distribution statistics.
        
        This is the main forecasting method that returns useful statistics.
        
        Args:
            params: Calibrated parameters
            horizon_days: Days into the future
            n_paths: Number of simulation paths
            percentiles: Custom percentiles (default: [5, 25, 50, 75, 95])
            
        Returns:
            Dictionary with forecast statistics:
            {
                "mean": 175.50,
                "median": 174.20,
                "std": 15.30,
                "percentiles": {
                    "p05": 150.00,
                    "p25": 165.00,
                    "p50": 174.20,
                    "p75": 185.00,
                    "p95": 205.00
                },
                "var_95": 25.50,  # Value at Risk
                "probability_above_S0": 0.52,  # Prob of gain
                "expected_return": 0.025,  # Expected % return
                "horizon_days": 30,
                "n_paths": 10000
            }
        """
        if percentiles is None:
            percentiles = [5, 25, 50, 75, 95]
        
        logger.info(f"Forecasting {horizon_days} days with {n_paths} paths")
        
        # Simulate terminal prices
        terminal_prices = self.simulate(
            params, horizon_days, n_paths, return_paths=False
        )
        
        # Convert to numpy for statistics
        prices_np = terminal_prices.cpu().numpy()
        
        # Calculate statistics
        mean_price = float(np.mean(prices_np))
        median_price = float(np.median(prices_np))
        std_price = float(np.std(prices_np))
        
        # Percentiles
        percentile_dict = {}
        for p in percentiles:
            percentile_dict[f"p{int(p):02d}"] = float(np.percentile(prices_np, p))
        
        # Value at Risk (95% - how much could we lose?)
        var_95 = params.S0 - percentile_dict["p05"]
        
        # Probability of gain
        prob_above_s0 = float(np.mean(prices_np > params.S0))
        
        # Expected return
        expected_return = (mean_price - params.S0) / params.S0
        
        result = {
            "mean": mean_price,
            "median": median_price,
            "std": std_price,
            "percentiles": percentile_dict,
            "var_95": var_95,
            "cvar_95": params.S0 - float(np.mean(prices_np[prices_np <= percentile_dict["p05"]])),
            "probability_above_S0": prob_above_s0,
            "expected_return": expected_return,
            "horizon_days": horizon_days,
            "n_paths": n_paths,
            "parameters": params.to_dict()
        }
        
        logger.info(
            f"Forecast complete: mean=${mean_price:.2f}, "
            f"95% CI=[${percentile_dict['p05']:.2f}, ${percentile_dict['p95']:.2f}]"
        )
        
        return result
    
    def forecast_with_paths(
        self,
        params: GBMParams,
        horizon_days: int,
        n_paths: int = 10000,
        n_sample_paths: int = 500
    ) -> Dict:
        """
        Generate forecast with sample paths for visualization.
        
        Args:
            params: Calibrated parameters
            horizon_days: Days into future
            n_paths: Total paths for statistics
            n_sample_paths: Number of sample paths to return for plotting
            
        Returns:
            Forecast dict with additional 'sample_paths' key containing
            a subset of paths for visualization
        """
        # Get statistics from all paths
        result = self.forecast(params, horizon_days, n_paths)
        
        # Generate sample paths for visualization
        sample_paths = self.simulate(
            params,
            horizon_days,
            n_paths=n_sample_paths,
            n_steps=horizon_days,  # Daily resolution
            return_paths=True
        )
        
        # Convert to list of lists for JSON
        result["sample_paths"] = sample_paths.cpu().numpy().tolist()
        result["n_sample_paths"] = n_sample_paths
        
        return result