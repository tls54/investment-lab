# Forecast Service Architecture Design

## Overview

This document outlines the proposed base model architecture for the forecast service, enabling multiple stochastic models with a consistent interface.

## Class Hierarchy

```
BaseForecaster (ABC)
    ├── GBMForecaster (implemented)
    ├── HestonForecaster (planned)
    ├── GARCHForecaster (future)
    ├── JumpDiffusionForecaster (future)
    └── RegimeSwitchingForecaster (future)
```

---

## Base Classes

### 1. ModelParams (Base Dataclass)

```python
from dataclasses import dataclass
from typing import Dict, Any
from abc import ABC, abstractmethod

@dataclass
class ModelParams(ABC):
    """
    Base class for all model parameters.

    Each model subclass defines its own parameters but all
    inherit common serialization/validation methods.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary for API response."""
        pass

    @abstractmethod
    def validate(self) -> None:
        """Validate parameter constraints (e.g., sigma > 0)."""
        pass

    def __post_init__(self):
        """Auto-validate after initialization."""
        self.validate()


@dataclass
class GBMParams(ModelParams):
    """Geometric Brownian Motion parameters."""
    mu: float      # Drift
    sigma: float   # Volatility
    S0: float      # Initial price

    def validate(self) -> None:
        if self.sigma <= 0:
            raise ValueError("sigma must be positive")
        if self.S0 <= 0:
            raise ValueError("S0 must be positive")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mu": self.mu,
            "sigma": self.sigma,
            "S0": self.S0,
            "interpretation": {
                "annual_return": f"{self.mu * 100:.2f}%",
                "annual_volatility": f"{self.sigma * 100:.2f}%"
            }
        }


@dataclass
class HestonParams(ModelParams):
    """Heston stochastic volatility parameters."""
    mu: float       # Drift
    v0: float       # Initial variance
    kappa: float    # Mean reversion speed
    theta: float    # Long-term variance
    xi: float       # Vol of vol
    rho: float      # Correlation
    S0: float       # Initial price

    def validate(self) -> None:
        if self.v0 <= 0 or self.theta <= 0:
            raise ValueError("Variances must be positive")
        if self.kappa <= 0:
            raise ValueError("kappa must be positive")
        if not -1 <= self.rho <= 1:
            raise ValueError("rho must be in [-1, 1]")
        # Feller condition: 2*kappa*theta > xi^2
        if 2 * self.kappa * self.theta <= self.xi ** 2:
            raise ValueError("Feller condition violated: 2κθ > ξ²")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mu": self.mu,
            "v0": self.v0,
            "kappa": self.kappa,
            "theta": self.theta,
            "xi": self.xi,
            "rho": self.rho,
            "S0": self.S0
        }
```

---

### 2. ForecastResult (Standardized Output)

```python
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class ForecastResult:
    """
    Standardized forecast result returned by all models.

    This ensures consistent API responses regardless of model used.
    """

    # Metadata
    model_name: str
    symbol: str
    timestamp: datetime
    horizon_days: int
    n_paths: int

    # Current state
    current_price: float

    # Forecast distribution
    mean: float
    median: float
    std: float
    percentiles: Dict[str, float]  # {"p05": 150.0, "p50": 175.0, ...}

    # Risk metrics
    var_95: float                    # Value at Risk
    cvar_95: float                   # Conditional VaR
    probability_above_current: float # P(S_T > S_0)
    expected_return: float           # (E[S_T] - S_0) / S_0

    # Model parameters
    parameters: Dict[str, Any]

    # Calibration info
    calibration_period: Dict[str, Any]

    # Optional visualization data
    sample_paths: Optional[List[List[float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API response."""
        return {
            "model": self.model_name,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "horizon_days": self.horizon_days,
            "n_paths": self.n_paths,
            "current_price": self.current_price,
            "forecast": {
                "mean": self.mean,
                "median": self.median,
                "std": self.std,
                "percentiles": self.percentiles
            },
            "risk": {
                "var_95": self.var_95,
                "cvar_95": self.cvar_95,
                "probability_above_current": self.probability_above_current,
                "expected_return": self.expected_return
            },
            "parameters": self.parameters,
            "calibration": self.calibration_period,
            "sample_paths": self.sample_paths
        }
```

---

### 3. BaseForecaster (Abstract Base)

```python
import torch
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseForecaster(ABC):
    """
    Abstract base class for all price forecasting models.

    All forecasters must implement:
    - calibrate(): Estimate parameters from historical data
    - simulate(): Run Monte Carlo simulation
    - forecast(): Generate forecast statistics

    Common functionality provided:
    - GPU/CPU device management
    - Result caching (future)
    - Input validation
    - Statistics computation
    """

    def __init__(
        self,
        use_gpu: bool = True,
        cache_results: bool = False
    ):
        """
        Initialize forecaster.

        Args:
            use_gpu: Use GPU acceleration if available
            cache_results: Cache forecast results (requires Redis)
        """
        # Select best available device (MPS for Apple Silicon, CUDA for NVIDIA, or CPU)
        self.device = self._select_device(use_gpu)
        self.cache_results = cache_results
        self.model_name = self.__class__.__name__.replace("Forecaster", "")

        logger.info(
            f"{self.model_name} initialized on device: {self.device}"
        )

    @staticmethod
    def _select_device(use_gpu: bool) -> torch.device:
        """
        Select the best available compute device.

        Priority:
        1. MPS (Apple Silicon GPU) - M1/M2/M3 Macs
        2. CUDA (NVIDIA GPU) - Most deep learning workstations
        3. CPU - Fallback

        Args:
            use_gpu: Whether to use GPU if available

        Returns:
            torch.device instance
        """
        if not use_gpu:
            return torch.device("cpu")

        # Check for Apple Silicon GPU (Metal Performance Shaders)
        if torch.backends.mps.is_available():
            try:
                # Verify MPS is actually working (sometimes is_available() lies)
                _ = torch.zeros(1, device="mps")
                return torch.device("mps")
            except Exception:
                logger.warning("MPS reported available but failed test, falling back")

        # Check for NVIDIA GPU (CUDA)
        if torch.cuda.is_available():
            return torch.device("cuda")

        # Fallback to CPU
        return torch.device("cpu")

    @abstractmethod
    def calibrate(
        self,
        prices: np.ndarray,
        trading_days_per_year: int = 252
    ) -> ModelParams:
        """
        Calibrate model parameters from historical prices.

        Args:
            prices: Array of historical prices (oldest first)
            trading_days_per_year: For annualization

        Returns:
            Calibrated model parameters

        Raises:
            ValueError: If insufficient data
        """
        pass

    @abstractmethod
    def simulate(
        self,
        params: ModelParams,
        horizon_days: int,
        n_paths: int = 10000,
        n_steps: Optional[int] = None,
        return_paths: bool = False
    ) -> torch.Tensor:
        """
        Simulate price paths using Monte Carlo.

        Args:
            params: Calibrated parameters
            horizon_days: Forecast horizon in days
            n_paths: Number of simulation paths
            n_steps: Time steps (default: horizon_days)
            return_paths: Return full paths or just terminal values

        Returns:
            Tensor of shape (n_paths,) or (n_paths, n_steps+1)
        """
        pass

    def forecast(
        self,
        params: ModelParams,
        horizon_days: int,
        n_paths: int = 10000,
        percentiles: Optional[List[float]] = None,
        symbol: str = "UNKNOWN"
    ) -> ForecastResult:
        """
        Generate forecast statistics.

        This method is implemented in the base class and uses
        the subclass's simulate() method.

        Args:
            params: Calibrated parameters
            horizon_days: Days into future
            n_paths: Number of simulation paths
            percentiles: Custom percentiles
            symbol: Asset symbol for metadata

        Returns:
            Standardized ForecastResult
        """
        if percentiles is None:
            percentiles = [5, 25, 50, 75, 95]

        logger.info(
            f"{self.model_name}: Forecasting {symbol} "
            f"{horizon_days} days with {n_paths} paths"
        )

        # Run simulation (calls subclass implementation)
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
            percentile_dict[f"p{int(p):02d}"] = float(
                np.percentile(prices_np, p)
            )

        # Risk metrics
        p05 = percentile_dict["p05"]
        var_95 = params.S0 - p05
        cvar_95 = params.S0 - float(
            np.mean(prices_np[prices_np <= p05])
        )
        prob_above = float(np.mean(prices_np > params.S0))
        expected_return = (mean_price - params.S0) / params.S0

        result = ForecastResult(
            model_name=self.model_name,
            symbol=symbol,
            timestamp=datetime.now(),
            horizon_days=horizon_days,
            n_paths=n_paths,
            current_price=params.S0,
            mean=mean_price,
            median=median_price,
            std=std_price,
            percentiles=percentile_dict,
            var_95=var_95,
            cvar_95=cvar_95,
            probability_above_current=prob_above,
            expected_return=expected_return,
            parameters=params.to_dict(),
            calibration_period={}  # To be filled by caller
        )

        logger.info(
            f"{self.model_name}: Complete. "
            f"mean=${mean_price:.2f}, "
            f"95% CI=[${p05:.2f}, ${percentile_dict['p95']:.2f}]"
        )

        return result

    def forecast_with_paths(
        self,
        params: ModelParams,
        horizon_days: int,
        n_paths: int = 10000,
        n_sample_paths: int = 100,
        symbol: str = "UNKNOWN"
    ) -> ForecastResult:
        """
        Generate forecast with sample paths for visualization.

        Args:
            params: Calibrated parameters
            horizon_days: Days into future
            n_paths: Total paths for statistics
            n_sample_paths: Paths to return for plotting
            symbol: Asset symbol

        Returns:
            ForecastResult with sample_paths populated
        """
        # Get statistics from all paths
        result = self.forecast(params, horizon_days, n_paths, symbol=symbol)

        # Generate sample paths
        sample_paths = self.simulate(
            params,
            horizon_days,
            n_paths=n_sample_paths,
            n_steps=horizon_days,
            return_paths=True
        )

        # Add to result
        result.sample_paths = sample_paths.cpu().numpy().tolist()

        return result

    def validate_prices(self, prices: np.ndarray, min_length: int = 30):
        """
        Validate input price data.

        Args:
            prices: Array of prices
            min_length: Minimum required data points

        Raises:
            ValueError: If data is invalid
        """
        if len(prices) < min_length:
            raise ValueError(
                f"Insufficient data: {len(prices)} prices provided, "
                f"need at least {min_length}"
            )

        if np.any(prices <= 0):
            raise ValueError("Prices must be positive")

        if np.any(np.isnan(prices)) or np.any(np.isinf(prices)):
            raise ValueError("Prices contain NaN or Inf values")
```

---

## Refactored GBM Using Base Class

```python
from .base import BaseForecaster, ModelParams
from dataclasses import dataclass
import numpy as np
import torch


class GBMForecaster(BaseForecaster):
    """
    Geometric Brownian Motion forecaster.

    Now inherits common functionality from BaseForecaster.
    Only needs to implement calibrate() and simulate().
    """

    def calibrate(
        self,
        prices: np.ndarray,
        trading_days_per_year: int = 252
    ) -> GBMParams:
        """Calibrate GBM using MLE."""
        # Validate input
        self.validate_prices(prices)

        # Calculate log returns
        log_returns = np.diff(np.log(prices))
        dt = 1 / trading_days_per_year

        # MLE estimates
        mean_log_return = np.mean(log_returns)
        std_log_return = np.std(log_returns, ddof=1)

        mu = mean_log_return / dt + 0.5 * (std_log_return / np.sqrt(dt)) ** 2
        sigma = std_log_return / np.sqrt(dt)
        S0 = float(prices[-1])

        return GBMParams(mu=mu, sigma=sigma, S0=S0)

    def simulate(
        self,
        params: GBMParams,  # Type-specific
        horizon_days: int,
        n_paths: int = 10000,
        n_steps: Optional[int] = None,
        return_paths: bool = False
    ) -> torch.Tensor:
        """Simulate GBM paths."""
        if n_steps is None:
            n_steps = horizon_days

        T = horizon_days / 252
        dt = T / n_steps

        # Move to GPU
        S0 = torch.tensor(params.S0, device=self.device, dtype=torch.float32)
        mu = torch.tensor(params.mu, device=self.device, dtype=torch.float32)
        sigma = torch.tensor(params.sigma, device=self.device, dtype=torch.float32)

        if return_paths:
            # Full paths
            paths = torch.zeros(n_paths, n_steps + 1, device=self.device)
            paths[:, 0] = S0

            Z = torch.randn(n_paths, n_steps, device=self.device)
            drift = (mu - 0.5 * sigma ** 2) * dt
            diffusion = sigma * np.sqrt(dt)

            for t in range(n_steps):
                paths[:, t + 1] = paths[:, t] * torch.exp(
                    drift + diffusion * Z[:, t]
                )

            return paths
        else:
            # Terminal values only
            Z = torch.randn(n_paths, n_steps, device=self.device)
            total_shock = Z.sum(dim=1)

            drift = (mu - 0.5 * sigma ** 2) * T
            diffusion = sigma * np.sqrt(dt) * total_shock

            return S0 * torch.exp(drift + diffusion)
```

---

## Benefits of This Architecture

### 1. **Consistency**
All models return `ForecastResult` with the same structure:
```python
# Works with any model
forecaster = GBMForecaster()  # or HestonForecaster()
result = forecaster.forecast(params, horizon_days=30)

# Always has the same fields
print(result.mean)
print(result.var_95)
print(result.parameters)
```

### 2. **Polymorphism in API**
```python
# In forecasts.py router:

MODEL_REGISTRY = {
    "gbm": GBMForecaster,
    "heston": HestonForecaster,
    "garch": GARCHForecaster
}

@router.post("/forecast/{model_name}")
async def forecast(model_name: str, request: ForecastRequest):
    """Works for any registered model!"""

    # Get the right forecaster class
    forecaster_class = MODEL_REGISTRY.get(model_name)
    if not forecaster_class:
        raise HTTPException(404, f"Model '{model_name}' not found")

    # Create instance
    forecaster = forecaster_class(use_gpu=True)

    # Rest of code is identical for all models!
    params = forecaster.calibrate(prices)
    result = forecaster.forecast(params, request.horizon_days, request.n_paths)

    return result.to_dict()
```

### 3. **Easy to Add Models**
Adding Heston becomes trivial:
```python
class HestonForecaster(BaseForecaster):
    """Just implement calibrate() and simulate()."""

    def calibrate(self, prices, trading_days_per_year=252) -> HestonParams:
        # Method of moments + optimization
        ...
        return HestonParams(...)

    def simulate(self, params: HestonParams, ...) -> torch.Tensor:
        # Euler-Maruyama with full truncation
        ...
        return paths

# That's it! All other functionality inherited
```

### 4. **Type Safety**
```python
def run_forecast(
    forecaster: BaseForecaster,  # Any forecaster
    prices: np.ndarray,
    horizon: int
) -> ForecastResult:
    """Type hints work perfectly."""
    params = forecaster.calibrate(prices)
    return forecaster.forecast(params, horizon)

# IDE knows what methods are available
# Type checker verifies correct usage
```

### 5. **Testing**
```python
# Test that works for ANY forecaster
@pytest.mark.parametrize("forecaster_class", [
    GBMForecaster,
    HestonForecaster,
    GARCHForecaster
])
def test_forecast_distribution(forecaster_class):
    """Test applies to all models."""
    forecaster = forecaster_class(use_gpu=False)

    # Generate synthetic data
    prices = generate_test_prices()

    # Calibrate and forecast
    params = forecaster.calibrate(prices)
    result = forecaster.forecast(params, horizon_days=30, n_paths=10000)

    # All models must satisfy these properties
    assert result.mean > 0
    assert result.percentiles["p05"] < result.percentiles["p95"]
    assert 0 <= result.probability_above_current <= 1
```

---

## Migration Path

**Step 1:** Create base classes (1-2 days)
- `base.py` with `BaseForecaster`, `ModelParams`, `ForecastResult`

**Step 2:** Refactor GBM (1 day)
- Make `GBMForecaster` inherit from `BaseForecaster`
- Remove duplicated code (statistics, validation)

**Step 3:** Add Heston (2-3 days)
- Port from Research notebooks
- Implement `HestonForecaster(BaseForecaster)`

**Step 4:** Update API (1 day)
- Add model registry
- Make endpoints model-agnostic

**Total:** ~1 week effort

---

## Summary

**Without base class:**
- Each model has its own interface
- Duplicated code (validation, statistics, GPU management)
- Hard to add new models
- API needs custom code for each model

**With base class:**
- ✅ Consistent interface
- ✅ Code reuse (write once, use everywhere)
- ✅ Easy to extend (new model = 2 methods)
- ✅ Type-safe polymorphism
- ✅ Cleaner API code
- ✅ Better testing

**The investment pays off when adding model #2 (Heston). By model #3 (GARCH), you're saving massive amounts of time.**
