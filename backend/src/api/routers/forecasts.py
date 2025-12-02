"""
Forecast endpoints for Investment Lab API.

Provides price forecasting using stochastic models.
"""

import numpy as np
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

# Import configuration
from ...core.config import settings

# Import our fetchers and forecasting
from ...price_service.fetchers import YFinanceFetcher
from ...price_service.models import AssetType, SymbolNotFoundError
from ...forecast_service.models.gbm import GBMModel


router = APIRouter()

# Initialize model (reuse across requests)
gbm_model = GBMModel(use_gpu=True)

# Initialize fetchers
fetchers = {
    "yfinance": YFinanceFetcher(),
}


# Request/Response models for API
class ForecastRequest(BaseModel):
    """Request model for forecasting."""
    symbol: str = Field(..., description="Asset symbol (e.g., AAPL, BTC)")
    horizon_days: int = Field(..., ge=1, le=365, description="Forecast horizon in days (1-365)")
    n_paths: int = Field(100000, ge=1000, le=5000000, description="Number of Monte Carlo paths (1k-100k)")
    calibration_days: int = Field(252, ge=30, le=2000, description="Days of historical data for calibration")
    asset_type: Optional[AssetType] = Field(None, description="Asset type (auto-detect if None)")
    include_paths: bool = Field(False, description="Include sample paths for visualization")
    n_sample_paths: int = Field(500, ge=10, le=5000, description="Number of sample paths if include_paths=True")


class ForecastResponse(BaseModel):
    """Response model for forecasting."""
    symbol: str
    current_price: float
    horizon_days: int
    n_paths: int
    
    # Forecast statistics
    mean: float
    median: float
    std: float
    percentiles: dict
    
    # Risk metrics
    var_95: float
    cvar_95: float
    probability_above_current: float
    expected_return: float
    
    # Model info
    parameters: dict
    calibration_period: dict
    
    # Optional: sample paths
    sample_paths: Optional[List[List[float]]] = None


# ============================================================================
# ENDPOINT 1: Forecast Price with GBM
# ============================================================================

@router.post("/forecast/gbm", response_model=ForecastResponse)
async def forecast_gbm(request: ForecastRequest):
    """
    Forecast asset price using Geometric Brownian Motion (GBM).
    
    GBM assumes constant drift and volatility. Best for short-term
    forecasts (days to weeks) in stable market conditions.
    
    **How it works:**
    1. Fetches historical prices for calibration
    2. Estimates drift (μ) and volatility (σ) parameters
    3. Runs Monte Carlo simulation (10k-100k paths)
    4. Returns distribution statistics and risk metrics
    
    **Example Request:**
    ```json
    {
        "symbol": "AAPL",
        "horizon_days": 30,
        "n_paths": 10000,
        "calibration_days": 252,
        "include_paths": false
    }
    ```
    
    **Example Response:**
    ```json
    {
        "symbol": "AAPL",
        "current_price": 175.50,
        "horizon_days": 30,
        "mean": 178.20,
        "median": 177.80,
        "std": 12.50,
        "percentiles": {
            "p05": 158.30,
            "p50": 177.80,
            "p95": 200.40
        },
        "var_95": 17.20,
        "probability_above_current": 0.52,
        "expected_return": 0.015,
        "parameters": {
            "mu": 0.08,
            "sigma": 0.25,
            "S0": 175.50
        }
    }
    ```
    
    **Use Cases:**
    - Risk assessment: "What's my 95% worst case?"
    - Target setting: "50% chance price is above X"
    - Comparison: "Which stock has higher upside?"
    
    **Parameters:**
    - `symbol`: Stock or crypto symbol
    - `horizon_days`: How many days ahead (1-365)
    - `n_paths`: More paths = more accurate (10k is usually enough)
    - `calibration_days`: Historical data window (252 = 1 year)
    - `include_paths`: Set to true to get sample paths for charts
    
    **Limitations:**
    - Assumes constant volatility (not true in crashes)
    - No jumps or regime changes
    - Historical patterns may not repeat
    - Longer horizons = less reliable
    """
    try:
        # Use yfinance for all asset types (stocks, ETFs, crypto)
        fetcher = fetchers["yfinance"]

        # Fetch historical data for calibration
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.calibration_days)
        
        historical = await fetcher.fetch_historical(
            request.symbol,
            start_date,
            end_date,
            interval="1d",
            asset_type=request.asset_type
        )
        
        if len(historical.prices) < 30:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data: only {len(historical.prices)} days available. Need at least 30."
            )
        
        # Extract price array
        prices = np.array([p.price for p in historical.prices])
        current_price = float(prices[-1])
        
        # Calibrate GBM parameters
        params = gbm_model.calibrate(prices)
        
        # Generate forecast
        if request.include_paths:
            result = gbm_model.forecast_with_paths(
                params,
                request.horizon_days,
                request.n_paths,
                request.n_sample_paths
            )
        else:
            result = gbm_model.forecast(
                params,
                request.horizon_days,
                request.n_paths
            )
        
        # Build response
        return ForecastResponse(
            symbol=request.symbol,
            current_price=current_price,
            horizon_days=request.horizon_days,
            n_paths=request.n_paths,
            mean=result["mean"],
            median=result["median"],
            std=result["std"],
            percentiles=result["percentiles"],
            var_95=result["var_95"],
            cvar_95=result["cvar_95"],
            probability_above_current=result["probability_above_S0"],
            expected_return=result["expected_return"],
            parameters=result["parameters"],
            calibration_period={
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": len(prices)
            },
            sample_paths=result.get("sample_paths")
        )
    
    except SymbolNotFoundError:
        raise HTTPException(status_code=404, detail=f"Symbol '{request.symbol}' not found")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


# ============================================================================
# ENDPOINT 2: Quick Forecast (GET method for simplicity)
# ============================================================================

@router.get("/forecast/gbm/{symbol}")
async def quick_forecast(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Forecast horizon in days"),
    asset_type: Optional[AssetType] = Query(None, description="Asset type")
):
    """
    Quick forecast with default parameters.
    
    Simpler endpoint for getting a forecast without POST request.
    Uses sensible defaults: 10k paths, 1 year calibration.
    
    **Examples:**
    - `/api/forecast/gbm/AAPL` - 30-day forecast for Apple
    - `/api/forecast/gbm/BTC?days=7&asset_type=crypto` - 7-day BTC forecast
    - `/api/forecast/gbm/MSFT?days=90` - 90-day Microsoft forecast
    
    **Returns:**
    Same as POST endpoint but without sample paths.
    """
    request = ForecastRequest(
        symbol=symbol,
        horizon_days=days,
        n_paths=10000,
        calibration_days=252,
        asset_type=asset_type,
        include_paths=False
    )
    
    return await forecast_gbm(request)


