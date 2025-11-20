# Investment Lab - Project Roadmap

> **Last Updated:** November 7, 2025  
> **Status:** Planning Phase  
> **Timeline:** Long-term personal project (flexible)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Sources](#data-sources)
- [Implementation Phases](#implementation-phases)
- [Project Structure](#project-structure)
- [Technical Decisions](#technical-decisions)
- [Testing Strategy](#testing-strategy)
- [Performance Targets](#performance-targets)
- [Future Features](#future-features)

---

## Project Overview

**Investment Lab** is a comprehensive financial analysis platform that combines real-time market data with advanced quantitative modeling. The platform enables users to visualize asset prices in arbitrary denominations and generate probabilistic price forecasts using stochastic models.

### Vision

Build a modular, extensible platform that serves as both a practical investment analysis tool and a laboratory for implementing advanced financial models and ML techniques.

### Core Principles

- **Extensibility**: Easy to add new models, data sources, and features
- **Performance**: GPU acceleration for compute-intensive operations
- **Reliability**: Comprehensive testing and error handling
- **Usability**: Intuitive UI with real-time updates
- **Learning**: Document implementation details for educational value

---

## Core Features

### Feature 1: Denominational Pricing & Visualization

**Description:** View any asset priced in terms of any other asset, not just fiat currencies.

**Examples:**
- S&P 500 priced in Gold (SPX/GC)
- Tesla priced in Bitcoin (TSLA/BTC)
- Ethereum priced in Apple stock (ETH/AAPL)

**Components:**
- Real-time price fetching from multiple data sources
- Automatic denomination conversion with caching
- Interactive charts with TradingView-style UI
- WebSocket streaming for live updates
- Historical data visualization
- Multi-asset comparison view

**Technical Challenges:**
- Rate limiting across multiple APIs
- Synchronized price updates for conversion
- Efficient caching strategy
- WebSocket connection management

---

### Feature 2: Stochastic Price Forecasting

**Description:** Generate probabilistic price forecasts using Geometric Brownian Motion (GBM) and Heston stochastic volatility models.

**Capabilities:**
- Monte Carlo simulation with 10k-1M+ paths
- Parameter calibration from historical data
- Distribution analysis at target horizon
- Confidence intervals and percentiles
- Value at Risk (VaR) and Conditional VaR (CVaR)
- Sample path visualization

**Models:**

#### Geometric Brownian Motion (GBM)
```
dS_t = μ S_t dt + σ S_t dW_t

Parameters:
- μ (mu): Drift (expected return)
- σ (sigma): Volatility

Calibration: Maximum Likelihood Estimation from log returns
```

#### Heston Stochastic Volatility
```
dS_t = μ S_t dt + √v_t S_t dW_t^S
dv_t = κ(θ - v_t)dt + ξ√v_t dW_t^v

Parameters:
- μ: Drift
- v_0: Initial variance
- κ (kappa): Mean reversion speed
- θ (theta): Long-term variance
- ξ (xi): Volatility of volatility
- ρ (rho): Correlation between price and volatility

Calibration: Method of moments + optimization
```

**Technical Implementation:**
- PyTorch for GPU-accelerated Monte Carlo
- Euler-Maruyama discretization scheme
- Full truncation for variance positivity
- Correlated Brownian motion generation
- Background task processing for large simulations
- Results caching with Redis

**Technical Challenges:**
- Numerical stability in stochastic simulation
- GPU memory management for large path counts
- Efficient parameter calibration
- Validation against analytical solutions where available

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                            │
│  React + TypeScript (Vibe coded)                            │
│  - TradingView-style charts (lightweight-charts)            │
│  - Real-time WebSocket updates                              │
│  - Interactive denomination picker                          │
│  - Monte Carlo visualization (distribution plots)           │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST/WebSocket
┌──────────────────────┴──────────────────────────────────────┐
│                   FastAPI Gateway                            │
│  - Auth/Rate limiting (future)                              │
│  - Request routing                                          │
│  - WebSocket manager                                        │
│  - CORS & security headers                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
        ┃                              ┃
┌───────▼────────┐            ┌────────▼────────┐
│  Price Service │            │ Forecast Service│
│                │            │                 │
│ - Data fetching│            │ - GBM engine    │
│ - Conversion   │            │ - Heston engine │
│ - Caching      │            │ - PyTorch accel │
│ - WebSocket pub│            │ - Result cache  │
│ - API clients  │            │ - Calibration   │
└───────┬────────┘            └────────┬────────┘
        │                              │
        ↓                              ↓
┌────────────────┐            ┌─────────────────┐
│  Data Layer    │            │  Compute Layer  │
│                │            │                 │
│ - Redis cache  │            │ - GPU scheduler │
│ - TimescaleDB  │            │ - Task queue    │
│ - API clients  │            │ - C++ modules*  │
│ - Rate limiters│            │   (future)      │
└────────────────┘            └─────────────────┘
```

### Service Responsibilities

**Frontend:**
- User interaction and visualization
- State management (Zustand)
- API communication (TanStack Query)
- WebSocket connection handling
- Responsive design

**FastAPI Gateway:**
- Request validation and routing
- WebSocket connection management
- Rate limiting and authentication
- CORS and security
- Error handling and logging

**Price Service:**
- Multi-source data fetching (stocks, crypto, commodities)
- Denomination conversion logic
- Intelligent caching strategies
- Real-time price streaming
- Historical data management

**Forecast Service:**
- Model implementations (GBM, Heston)
- Parameter calibration
- Monte Carlo simulation
- GPU workload management
- Asynchronous task processing
- Results caching and retrieval

**Data Layer:**
- Redis for high-speed caching and pub/sub
- TimescaleDB for time-series storage
- Connection pooling
- Query optimization

**Compute Layer:**
- PyTorch GPU acceleration
- Celery task queue for long-running jobs
- GPU memory management
- Future: C++ integration via pybind11

---

## Tech Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | FastAPI | 0.104+ | REST API & WebSocket |
| Language | Python | 3.13 | Primary language |
| Validation | Pydantic | V2 | Data validation |
| Database | PostgreSQL/TimescaleDB | 15+ | Time-series storage |
| Cache | Redis | 7+ | Caching & pub/sub |
| ORM | SQLAlchemy | 2.0+ | Database interface |
| Tasks | Celery | 5.3+ | Background jobs |
| HTTP Client | httpx | 0.24+ | Async API calls |
| Compute | PyTorch | 2.0+ | GPU acceleration |
| Numerical | NumPy, Pandas | Latest | Data processing |
| Testing | pytest | Latest | Unit/integration tests |
| Type Checking | mypy | Latest | Static type checking |
| Linting | ruff | Latest | Code quality |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 18+ | UI framework |
| Language | TypeScript | 5+ | Type safety |
| Build Tool | Vite | 5+ | Fast builds |
| Data Fetching | TanStack Query | 5+ | Server state |
| Charting | lightweight-charts | 4+ | Price charts |
| Viz | Plotly/Recharts | Latest | Distributions |
| Styling | Tailwind CSS | 3+ | Styling |
| State | Zustand | 4+ | Client state |
| Testing | Vitest | Latest | Unit tests |
| E2E | Playwright | Latest | Integration tests |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker | Development & deployment |
| Orchestration | Docker Compose | Local multi-service |
| Dependency Mgmt | Poetry/uv | Python packages |
| CI/CD | GitHub Actions | Automation |
| Future: C++ | pybind11 | Python bindings |
| Future: C++ Compiler | GCC/Clang with C++17 | Native extensions |

---

## Data Sources

### Recommended APIs

| Asset Class | Primary API | Backup | Rate Limits | Notes |
|-------------|-------------|---------|-------------|-------|
| **Stocks** | yfinance | Alpha Vantage | No limits (free) | Free, no API key required |
| **Crypto** | yfinance | Binance API | No limits (free) | Supports major cryptos via -USD suffix |
| **Commodities** | Alpha Vantage | Polygon.io | 500 calls/day (free) | Gold, Silver, Oil, etc. |
| **Forex** | Alpha Vantage | Fixer.io | 500 calls/day (free) | Currency conversions |

### Caching Strategy

| Data Type | Cache Duration | Rationale |
|-----------|----------------|-----------|
| Real-time quotes | 1-5 seconds | Balance freshness vs API limits |
| Intraday data | 1 minute | Sufficient for most use cases |
| Daily data | 1 hour | Rarely changes intraday |
| Historical data | 24 hours | Static data |
| Forecast results | 1 hour | Expensive computation |

### API Client Architecture

```python
# Base class for all data fetchers
class AssetFetcher(ABC):
    @abstractmethod
    async def fetch_price(self, symbol: str) -> Price:
        """Get current price for symbol"""
        pass
    
    @abstractmethod
    async def fetch_historical(
        self, 
        symbol: str, 
        start: datetime, 
        end: datetime
    ) -> List[Price]:
        """Get historical prices"""
        pass
    
    @abstractmethod
    async def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is valid"""
        pass
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-3)

**Goal:** Establish project structure, tooling, and basic data fetching capabilities.

#### Week 1: Project Setup
- [ ] Initialize Git repository with `.gitignore`
- [ ] Set up monorepo structure (or decide on multi-repo)
- [ ] Configure Poetry/uv for Python dependency management
- [ ] Create Docker Compose configuration
  - [ ] FastAPI service
  - [ ] Redis service
  - [ ] PostgreSQL/TimescaleDB service
  - [ ] Celery worker (optional for now)
- [ ] Initialize FastAPI project
  - [ ] Health check endpoints
  - [ ] Basic middleware (CORS, logging)
  - [ ] Configuration management (Pydantic Settings)
- [ ] Set up logging infrastructure
  - [ ] Structured logging (structlog)
  - [ ] Log levels and formatting
- [ ] GitHub Actions CI/CD
  - [ ] Linting (ruff)
  - [ ] Type checking (mypy)
  - [ ] Unit tests (pytest)
- [ ] Documentation setup
  - [ ] README.md with setup instructions
  - [ ] Contributing guidelines
  - [ ] API documentation (FastAPI automatic)

**Deliverable:** Working Docker Compose setup with FastAPI responding to health checks.

---

#### Week 2-3: Data Layer

**Price Data Models:**
```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    FOREX = "forex"

class Price(BaseModel):
    symbol: str
    asset_type: AssetType
    price: float
    timestamp: datetime
    currency: str = "USD"
    volume: Optional[float] = None
    source: str

class HistoricalPrice(BaseModel):
    symbol: str
    prices: List[Price]
    start_date: datetime
    end_date: datetime
```

**Tasks:**
- [ ] Define Pydantic models for price data
- [ ] Implement `AssetFetcher` abstract base class
- [ ] Create Alpha Vantage client
  - [ ] Stock price fetching
  - [ ] Historical data retrieval
  - [ ] Rate limiting
  - [ ] Error handling
- [ ] Create yfinance client
  - [ ] Stock/ETF data
  - [ ] Crypto price fetching (with -USD suffix)
  - [ ] Historical data
- [ ] Implement Redis caching layer
  - [ ] Cache keys strategy
  - [ ] TTL management
  - [ ] Cache invalidation
- [ ] Database schema design
  - [ ] Historical price storage
  - [ ] Asset metadata
  - [ ] User preferences (future)
- [ ] Unit tests for all fetchers
  - [ ] Mock API responses
  - [ ] Test error handling
  - [ ] Test rate limiting
- [ ] Integration tests
  - [ ] Real API calls (with VCR.py cassettes)
  - [ ] Cache behavior validation

**Deliverable:** Robust data fetching system that can retrieve and cache prices from multiple sources.

---

### Phase 2: Feature 1 - Denominational Pricing (Weeks 4-6)

**Goal:** Build the core pricing conversion feature with real-time visualization.

#### Week 4: Backend Implementation

**Denomination Converter:**
```python
class DenominationConverter:
    def __init__(self, cache: Redis, fetchers: Dict[AssetType, AssetFetcher]):
        self.cache = cache
        self.fetchers = fetchers
    
    async def convert(
        self, 
        asset: str, 
        denomination: str,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Convert asset price to denomination.
        
        Examples:
            - convert("AAPL", "BTC") -> AAPL price in Bitcoin
            - convert("SPY", "GLD") -> S&P 500 ETF in Gold ETF
        """
        # Fetch both prices (with caching)
        asset_price = await self._fetch_price(asset, timestamp)
        denom_price = await self._fetch_price(denomination, timestamp)
        
        return asset_price / denom_price
    
    async def convert_series(
        self,
        asset: str,
        denomination: str,
        start: datetime,
        end: datetime
    ) -> List[Tuple[datetime, float]]:
        """Convert historical price series"""
        pass
```

**Tasks:**
- [ ] Implement `DenominationConverter` class
- [ ] Create REST endpoints
  - [ ] `GET /api/price/{asset}` - Current price
  - [ ] `GET /api/price/{asset}/in/{denomination}` - Converted price
  - [ ] `GET /api/price/{asset}/history` - Historical prices
  - [ ] `GET /api/price/{asset}/in/{denomination}/history` - Converted history
- [ ] Implement WebSocket endpoints
  - [ ] `WS /ws/price/{asset}/{denomination}` - Real-time stream
  - [ ] Connection management
  - [ ] Heartbeat/ping-pong
  - [ ] Graceful disconnection
- [ ] Rate limiting middleware
  - [ ] Per-IP limits
  - [ ] Per-endpoint limits
- [ ] Error handling and validation
  - [ ] Invalid symbol handling
  - [ ] API failure fallbacks
  - [ ] User-friendly error messages
- [ ] Comprehensive testing
  - [ ] Unit tests for converter
  - [ ] Integration tests for endpoints
  - [ ] WebSocket connection tests

**Deliverable:** Working API that can serve real-time and historical denominational prices.

---

#### Week 5-6: Frontend Implementation

**Key Components:**
```typescript
// Asset search and selection
interface AssetSelectorProps {
  onSelect: (symbol: string, type: AssetType) => void;
  placeholder?: string;
}

// Denomination picker
interface DenominationPickerProps {
  current: string;
  onSwitch: (denomination: string) => void;
  favorites?: string[];
}

// Main price chart
interface PriceChartProps {
  asset: string;
  denomination: string;
  timeframe: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';
  realTime?: boolean;
}

// Multi-asset comparison
interface ComparisonViewProps {
  assets: Array<{symbol: string, denomination: string}>;
}
```

**Tasks:**
- [ ] Initialize React + TypeScript project with Vite
- [ ] Configure Tailwind CSS
- [ ] Set up TanStack Query for data fetching
- [ ] Implement `AssetSelector` component
  - [ ] Search functionality with debouncing
  - [ ] Asset type filtering
  - [ ] Recent selections
- [ ] Implement `DenominationPicker` component
  - [ ] Quick toggle between USD, BTC, Gold
  - [ ] Custom denomination input
  - [ ] Favorites management
- [ ] Implement `PriceChart` component
  - [ ] Integrate lightweight-charts
  - [ ] Timeframe selection
  - [ ] Crosshair with price info
  - [ ] Volume overlay (optional)
- [ ] Real-time WebSocket integration
  - [ ] Automatic reconnection
  - [ ] Connection status indicator
  - [ ] Smooth price updates
- [ ] Implement `ComparisonView` component
  - [ ] Multiple charts side-by-side
  - [ ] Synchronized crosshairs
  - [ ] Normalized view option
- [ ] Responsive design
  - [ ] Mobile-friendly layout
  - [ ] Touch interactions for charts
- [ ] Loading states and skeletons
- [ ] Error boundaries and error messages
- [ ] Dark mode support

**Deliverable:** Polished UI that allows users to visualize any asset in any denomination with real-time updates.

---

### Phase 3: Feature 2 - Forecasting (Weeks 7-11)

**Goal:** Implement stochastic models with GPU acceleration and intuitive visualization.

#### Week 7-8: GBM Implementation

**Model Structure:**
```python
from dataclasses import dataclass
import torch

@dataclass
class GBMParams:
    mu: float      # Drift (annualized)
    sigma: float   # Volatility (annualized)

class GBMModel:
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device(
            "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        )
    
    def calibrate(self, prices: np.ndarray) -> GBMParams:
        """
        Estimate GBM parameters from historical prices using MLE.
        
        Args:
            prices: Array of historical prices
            
        Returns:
            Calibrated parameters
        """
        log_returns = np.diff(np.log(prices))
        dt = 1 / 252  # Daily data, 252 trading days
        
        # MLE estimates
        mu = np.mean(log_returns) / dt + 0.5 * np.var(log_returns) / dt
        sigma = np.std(log_returns) / np.sqrt(dt)
        
        return GBMParams(mu=mu, sigma=sigma)
    
    def simulate(
        self,
        S0: float,
        T: float,
        params: GBMParams,
        n_paths: int = 10000,
        n_steps: int = 252,
        return_paths: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """
        Run Monte Carlo simulation using GPU acceleration.
        
        Args:
            S0: Initial price
            T: Time horizon (years)
            params: Model parameters
            n_paths: Number of simulation paths
            n_steps: Number of time steps
            return_paths: If True, return full paths; else just terminal values
            
        Returns:
            Terminal prices or (terminal prices, full paths)
        """
        dt = T / n_steps
        
        # Allocate on GPU
        if return_paths:
            S = torch.zeros(n_paths, n_steps + 1, device=self.device)
            S[:, 0] = S0
        else:
            S = torch.full((n_paths,), S0, device=self.device)
        
        # Generate random numbers on GPU
        Z = torch.randn(n_paths, n_steps, device=self.device)
        
        drift = (params.mu - 0.5 * params.sigma ** 2) * dt
        diffusion = params.sigma * np.sqrt(dt)
        
        if return_paths:
            for t in range(1, n_steps + 1):
                S[:, t] = S[:, t-1] * torch.exp(drift + diffusion * Z[:, t-1])
            return S.cpu().numpy()
        else:
            # More memory-efficient for terminal values only
            log_S = torch.log(S)
            log_S += drift * n_steps + diffusion * Z.sum(dim=1)
            return torch.exp(log_S).cpu().numpy()
    
    def forecast_distribution(
        self,
        S0: float,
        T: float,
        params: GBMParams,
        n_paths: int = 10000
    ) -> Dict[str, float]:
        """
        Generate forecast distribution statistics.
        
        Returns:
            Dictionary with mean, std, percentiles, VaR, CVaR
        """
        terminal_prices = self.simulate(S0, T, params, n_paths)
        
        return {
            'mean': float(np.mean(terminal_prices)),
            'median': float(np.median(terminal_prices)),
            'std': float(np.std(terminal_prices)),
            'p05': float(np.percentile(terminal_prices, 5)),
            'p25': float(np.percentile(terminal_prices, 25)),
            'p75': float(np.percentile(terminal_prices, 75)),
            'p95': float(np.percentile(terminal_prices, 95)),
            'var_95': float(S0 - np.percentile(terminal_prices, 5)),  # 95% VaR
            'cvar_95': float(S0 - np.mean(terminal_prices[terminal_prices <= np.percentile(terminal_prices, 5)])),
        }
```

**Tasks:**
- [ ] Implement GBM parameter calibration (MLE)
- [ ] Implement CPU-based Monte Carlo simulation
- [ ] Add PyTorch GPU acceleration
- [ ] Batch processing for memory efficiency
- [ ] Parameter validation and bounds checking
- [ ] Unit tests
  - [ ] Calibration accuracy on synthetic data
  - [ ] Simulation convergence tests
  - [ ] Chi-square goodness-of-fit tests
- [ ] Benchmarking
  - [ ] CPU vs GPU performance
  - [ ] Scaling with path count
  - [ ] Memory usage profiling

**Deliverable:** Production-ready GBM implementation with GPU acceleration.

---

#### Week 9-10: Heston Implementation

**Model Structure:**
```python
@dataclass
class HestonParams:
    mu: float       # Drift
    v0: float       # Initial variance
    kappa: float    # Mean reversion speed
    theta: float    # Long-term variance
    xi: float       # Vol of vol
    rho: float      # Correlation

class HestonModel:
    def __init__(self, use_gpu: bool = True):
        self.device = torch.device(
            "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        )
    
    def calibrate(
        self,
        prices: np.ndarray,
        initial_guess: Optional[HestonParams] = None
    ) -> HestonParams:
        """
        Calibrate Heston parameters using method of moments + optimization.
        
        This is more complex than GBM. We use:
        1. Method of moments for initial estimates
        2. scipy.optimize to refine
        """
        # Method of moments initial estimates
        log_returns = np.diff(np.log(prices))
        
        # ... implementation details
        
        # Optimization to refine parameters
        # Minimize distance between model-implied and empirical moments
        
        return optimized_params
    
    def simulate(
        self,
        S0: float,
        T: float,
        params: HestonParams,
        n_paths: int = 10000,
        n_steps: int = 252,
        return_paths: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Euler-Maruyama scheme with full truncation for variance.
        
        Returns terminal prices or (S_T, full price paths, full variance paths)
        """
        dt = T / n_steps
        
        # Initialize
        S = torch.zeros(n_paths, n_steps + 1, device=self.device)
        v = torch.zeros(n_paths, n_steps + 1, device=self.device)
        
        S[:, 0] = S0
        v[:, 0] = params.v0
        
        # Generate correlated Brownian motions
        Z1 = torch.randn(n_paths, n_steps, device=self.device)
        Z2 = torch.randn(n_paths, n_steps, device=self.device)
        
        W_S = Z1
        W_v = params.rho * Z1 + torch.sqrt(1 - params.rho**2) * Z2
        
        # Euler-Maruyama iteration
        for t in range(n_steps):
            # Full truncation: max(v_t, 0)
            v_pos = torch.maximum(v[:, t], torch.tensor(0.0, device=self.device))
            
            # Price evolution
            S[:, t+1] = S[:, t] * torch.exp(
                (params.mu - 0.5 * v_pos) * dt +
                torch.sqrt(v_pos * dt) * W_S[:, t]
            )
            
            # Variance evolution
            v[:, t+1] = v[:, t] + \
                        params.kappa * (params.theta - v_pos) * dt + \
                        params.xi * torch.sqrt(v_pos * dt) * W_v[:, t]
        
        if return_paths:
            return S.cpu().numpy(), v.cpu().numpy()
        else:
            return S[:, -1].cpu().numpy()
```

**Tasks:**
- [ ] Implement Heston parameter calibration
  - [ ] Method of moments
  - [ ] scipy.optimize integration
  - [ ] Constraint handling
- [ ] Implement Euler-Maruyama discretization
- [ ] GPU acceleration with PyTorch
- [ ] Variance positivity enforcement (full truncation)
- [ ] Correlated Brownian motion generation
- [ ] Unit tests
  - [ ] Calibration on known parameters
  - [ ] Mean reversion behavior validation
  - [ ] Correlation structure tests
- [ ] Validation against benchmarks
  - [ ] Compare with literature results
  - [ ] Semi-analytical solutions where available

**Deliverable:** Production-ready Heston implementation with accurate calibration.

---

#### Week 11: API & Frontend Integration

**API Endpoints:**
```python
# Forecast request/response models
class ForecastRequest(BaseModel):
    symbol: str
    model: Literal["gbm", "heston"]
    horizon_days: int  # Forecast horizon
    n_paths: int = 10000
    calibration_days: int = 252  # Historical data for calibration
    
class ForecastResponse(BaseModel):
    forecast_id: str
    status: Literal["pending", "completed", "failed"]
    progress: Optional[float]  # 0.0 to 1.0
    result: Optional[ForecastResult]

class ForecastResult(BaseModel):
    terminal_distribution: DistributionStats
    sample_paths: Optional[List[List[float]]]  # Optional path samples
    parameters: Dict[str, float]  # Calibrated parameters
    computation_time: float

# Endpoints
@router.post("/forecast/gbm", response_model=ForecastResponse)
async def forecast_gbm(
    request: ForecastRequest,
    background_tasks: BackgroundTasks
):
    """Submit GBM forecast request"""
    pass

@router.post("/forecast/heston", response_model=ForecastResponse)
async def forecast_heston(request: ForecastRequest):
    """Submit Heston forecast request"""
    pass

@router.get("/forecast/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(forecast_id: str):
    """Poll for forecast completion"""
    pass
```

**Frontend Components:**
```typescript
// Forecast configuration form
interface ForecastConfiguratorProps {
  symbol: string;
  onSubmit: (config: ForecastConfig) => void;
}

// Distribution visualization
interface DistributionChartProps {
  data: number[];  // Terminal prices
  currentPrice: number;
  stats: DistributionStats;
}

// Sample paths plot
interface PathVisualizerProps {
  paths: number[][];
  timestamps: Date[];
  currentPrice: number;
}

// Statistics panel
interface StatisticsPanelProps {
  stats: DistributionStats;
  params: ModelParameters;
}
```

**Tasks:**
- [ ] Implement FastAPI forecast endpoints
- [ ] Celery task for large simulations
  - [ ] Task definition
  - [ ] Progress tracking
  - [ ] Result storage in Redis
  - [ ] Error handling
- [ ] Result caching strategy
- [ ] Frontend: `ForecastConfigurator` component
  - [ ] Model selection (GBM/Heston)
  - [ ] Parameter inputs with validation
  - [ ] Horizon selection
  - [ ] Path count slider
- [ ] Frontend: `DistributionChart` component
  - [ ] Histogram with Plotly
  - [ ] Overlay current price
  - [ ] Percentile markers
  - [ ] VaR/CVaR visualization
- [ ] Frontend: `PathVisualizer` component
  - [ ] Sample path plotting
  - [ ] Mean path overlay
  - [ ] Confidence bands
- [ ] Frontend: `StatisticsPanel` component
  - [ ] Key statistics display
  - [ ] Model parameters
  - [ ] Computation time
- [ ] Polling mechanism for async forecasts
- [ ] Error handling and user feedback

**Deliverable:** Complete forecasting feature accessible through intuitive UI.

---

### Phase 4: Optimization & Enhancement (Weeks 12-15)

**Goal:** Refine performance, add polish, and optionally integrate C++ for maximum speed.

#### Week 12: Performance Optimization

**Tasks:**
- [ ] API performance benchmarking
  - [ ] ab (Apache Bench) or wrk for load testing
  - [ ] Identify bottlenecks with profiling
- [ ] Database query optimization
  - [ ] Add appropriate indices
  - [ ] Query plan analysis
  - [ ] Connection pooling tuning
- [ ] Redis caching improvements
  - [ ] Cache key optimization
  - [ ] Implement cache warming
  - [ ] Analyze hit/miss rates
- [ ] WebSocket optimization
  - [ ] Connection pooling
  - [ ] Message batching
  - [ ] Compression for large messages
- [ ] GPU optimization
  - [ ] Batch size tuning
  - [ ] Memory management
  - [ ] Multi-GPU support (optional)
- [ ] Frontend performance
  - [ ] Code splitting
  - [ ] Lazy loading
  - [ ] Chart render optimization
  - [ ] Bundle size analysis

**Performance Targets:**
- API endpoints: p95 latency < 200ms
- Price fetch (cached): < 50ms
- Price fetch (uncached): < 500ms
- GBM forecast (10k paths): < 1s on GPU
- Heston forecast (10k paths): < 3s on GPU
- WebSocket latency: < 100ms
- Frontend FCP: < 1.5s
- Frontend TTI: < 3s

---

#### Week 13-14: C++ Integration (Optional)

**Motivation:**
- Further performance gains for compute-heavy operations
- Learning experience with mixed-language systems
- Potential 2-5x speedup over PyTorch for some operations

**Architecture:**
```
Python (FastAPI) 
    ↓
pybind11 bindings
    ↓
C++ implementations (Eigen for linear algebra)
    ↓
OpenMP for parallelization
```

**Tasks:**
- [ ] Set up pybind11 build system
- [ ] Implement GBM in C++
  - [ ] Use Eigen for matrix operations
  - [ ] OpenMP for parallel path generation
  - [ ] Random number generation (std::mt19937)
- [ ] Implement Heston in C++
  - [ ] Correlated random number generation
  - [ ] Vectorized operations
- [ ] Python bindings
  - [ ] NumPy array interfacing
  - [ ] Error handling across language boundary
- [ ] Benchmarking
  - [ ] Compare with PyTorch implementation
  - [ ] Memory usage comparison
- [ ] Integration into FastAPI
  - [ ] Conditional compilation
  - [ ] Fallback to Python if C++ not available
- [ ] Testing
  - [ ] Numerical equivalence tests
  - [ ] Edge case handling

**Deliverable (Optional):** C++ accelerated models with Python bindings.

---

#### Week 15: Polish & UX Improvements

**Tasks:**
- [ ] Comprehensive error handling
  - [ ] User-friendly error messages
  - [ ] Retry logic for transient failures
  - [ ] Graceful degradation
- [ ] Loading states
  - [ ] Skeleton screens
  - [ ] Progress indicators
  - [ ] Smooth transitions
- [ ] Dark mode
  - [ ] Color scheme design
  - [ ] System preference detection
  - [ ] Persistent user preference
- [ ] Keyboard shortcuts
  - [ ] Asset search focus (/)
  - [ ] Quick denomination switch
  - [ ] Chart timeframe selection
- [ ] Accessibility
  - [ ] ARIA labels
  - [ ] Keyboard navigation
  - [ ] Screen reader support
- [ ] Mobile optimization
  - [ ] Touch-friendly controls
  - [ ] Responsive charts
  - [ ] Bottom sheet for mobile
- [ ] Documentation
  - [ ] User guide
  - [ ] Model explanations
  - [ ] API documentation
  - [ ] Code documentation

**Deliverable:** Production-quality application with excellent UX.

---

### Phase 5: Advanced Features (Weeks 16+)

**Goal:** Extend capabilities with sophisticated financial analysis and ML features.

#### Feature 3: Portfolio Analysis

**Capabilities:**
- Multi-asset portfolio construction
- Efficient frontier calculation
- Portfolio optimization (Markowitz, Black-Litterman)
- Risk metrics (VaR, CVaR, Beta, Sharpe ratio)
- Correlation analysis
- Rebalancing suggestions

**Implementation:**
- [ ] Portfolio data models
- [ ] Covariance matrix estimation
- [ ] Optimization engine (cvxpy)
- [ ] Efficient frontier computation
- [ ] Risk contribution analysis
- [ ] Frontend: Portfolio builder UI
- [ ] Frontend: Efficient frontier visualization
- [ ] Frontend: Risk dashboard

---

#### Feature 4: Options Pricing

**Capabilities:**
- Black-Scholes pricing for European options
- Heston semi-analytical pricing (Fourier methods)
- Greeks calculation (Delta, Gamma, Vega, Theta, Rho)
- Implied volatility calculation
- Volatility surface visualization

**Implementation:**
- [ ] Black-Scholes implementation
- [ ] Heston characteristic function
- [ ] Fourier inversion for pricing
- [ ] Numerical Greeks computation
- [ ] Implied volatility solver (Newton-Raphson)
- [ ] Frontend: Options calculator
- [ ] Frontend: Volatility surface 3D plot
- [ ] Frontend: Greeks dashboard

---

#### Feature 5: Machine Learning

**Capabilities:**
- LSTM price prediction
- Transformer-based models
- Sentiment analysis from news/social media
- Anomaly detection
- Feature importance analysis

**Implementation:**
- [ ] Data pipeline for ML features
- [ ] LSTM architecture with PyTorch
- [ ] Transformer implementation
- [ ] Sentiment analysis API integration
- [ ] Model training pipeline
- [ ] Hyperparameter tuning
- [ ] Model evaluation metrics
- [ ] Frontend: ML predictions dashboard
- [ ] Frontend: Feature importance visualization

---

#### Feature 6: Backtesting Engine

**Capabilities:**
- Custom strategy definition (DSL or Python)
- Historical simulation
- Performance metrics (returns, Sharpe, Sortino, max drawdown)
- Walk-forward analysis
- Parameter optimization
- Monte Carlo simulation of strategies

**Implementation:**
- [ ] Strategy DSL design
- [ ] Backtesting engine
- [ ] Performance calculator
- [ ] Walk-forward validator
- [ ] Parameter grid search
- [ ] Frontend: Strategy builder
- [ ] Frontend: Backtest results visualization
- [ ] Frontend: Equity curve plotting

---

#### Feature 7: Alert System

**Capabilities:**
- Price threshold alerts
- Technical indicator alerts (moving averages, RSI, etc.)
- Forecast-based alerts (e.g., 95th percentile exceeds target)
- Multi-channel delivery (email, SMS, push notifications)

**Implementation:**
- [ ] Alert rule engine
- [ ] Event detection system
- [ ] Notification service integration
  - [ ] Email (SendGrid)
  - [ ] SMS (Twilio)
  - [ ] Push (Firebase Cloud Messaging)
- [ ] Alert management API
- [ ] Frontend: Alert configuration UI
- [ ] Frontend: Alert history

---

#### Feature 8: Advanced Models

**Capabilities:**
- GARCH family for volatility modeling
- Jump diffusion models (Merton, Kou)
- Regime-switching models
- Fractional Brownian motion
- Variance Gamma process

**Implementation:**
- [ ] GARCH(1,1) implementation
- [ ] Jump diffusion calibration and simulation
- [ ] Hidden Markov Model for regime detection
- [ ] Fractional BM simulation (Cholesky method)
- [ ] Model comparison framework
- [ ] Frontend: Model selection and comparison

---

## Project Structure

```
investment-lab/
├── README.md
├── ROADMAP.md
├── docker-compose.yml
├── .gitignore
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       └── deploy.yml
│
├── backend/
│   ├── pyproject.toml
│   ├── poetry.lock / uv.lock
│   ├── Dockerfile
│   ├── .env.example
│   ├── alembic/              # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entry point
│   │   │
│   │   ├── api/              # API layer
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py
│   │   │   ├── middleware.py
│   │   │   └── routers/
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── prices.py
│   │   │       ├── forecasts.py
│   │   │       └── websocket.py
│   │   │
│   │   ├── price_service/    # Price fetching & conversion
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── converter.py
│   │   │   ├── cache.py
│   │   │   ├── fetchers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── alpha_vantage.py
│   │   │   │   └── yfinance_fetcher.py
│   │   │   └── stream.py     # WebSocket streaming
│   │   │
│   │   ├── forecast_service/ # Forecasting models
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── gbm.py
│   │   │   │   ├── heston.py
│   │   │   │   └── utils.py
│   │   │   ├── calibration/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mle.py
│   │   │   │   └── moments.py
│   │   │   ├── gpu_manager.py
│   │   │   └── tasks.py      # Celery tasks
│   │   │
│   │   ├── core/             # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py     # Settings (Pydantic)
│   │   │   ├── database.py   # SQLAlchemy setup
│   │   │   ├── redis.py      # Redis client
│   │   │   ├── logging.py    # Logging config
│   │   │   └── exceptions.py # Custom exceptions
│   │   │
│   │   └── tests/            # Tests
│   │       ├── __init__.py
│   │       ├── conftest.py
│   │       ├── unit/
│   │       ├── integration/
│   │       └── performance/
│   │
│   └── cpp_extensions/       # Optional C++ modules
│       ├── CMakeLists.txt
│       ├── src/
│       │   ├── gbm.cpp
│       │   ├── heston.cpp
│       │   └── utils.cpp
│       ├── include/
│       └── bindings.cpp      # pybind11 bindings
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── Dockerfile
│   ├── .env.example
│   ├── public/
│   │   ├── index.html
│   │   └── assets/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── vite-env.d.ts
│   │   │
│   │   ├── components/       # React components
│   │   │   ├── common/       # Reusable components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   └── Modal.tsx
│   │   │   ├── AssetSelector/
│   │   │   │   ├── index.tsx
│   │   │   │   └── AssetSelector.test.tsx
│   │   │   ├── DenominationPicker/
│   │   │   ├── PriceChart/
│   │   │   ├── ForecastConfigurator/
│   │   │   ├── DistributionChart/
│   │   │   ├── PathVisualizer/
│   │   │   └── StatisticsPanel/
│   │   │
│   │   ├── hooks/            # Custom React hooks
│   │   │   ├── useWebSocket.ts
│   │   │   ├── usePrice.ts
│   │   │   └── useForecast.ts
│   │   │
│   │   ├── api/              # API client
│   │   │   ├── client.ts
│   │   │   ├── prices.ts
│   │   │   └── forecasts.ts
│   │   │
│   │   ├── stores/           # State management
│   │   │   ├── useAppStore.ts
│   │   │   └── useSettingsStore.ts
│   │   │
│   │   ├── types/            # TypeScript types
│   │   │   ├── price.ts
│   │   │   ├── forecast.ts
│   │   │   └── api.ts
│   │   │
│   │   ├── utils/            # Utility functions
│   │   │   ├── format.ts
│   │   │   └── validation.ts
│   │   │
│   │   └── styles/           # Global styles
│   │       └── globals.css
│   │
│   └── tests/                # Frontend tests
│       ├── unit/
│       └── e2e/
│
├── docker/                   # Docker configurations
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   └── Dockerfile.frontend
│
└── docs/                     # Documentation
    ├── API.md
    ├── MODELS.md
    ├── DEPLOYMENT.md
    └── CONTRIBUTING.md
```

---

## Technical Decisions

### Why TimescaleDB over plain PostgreSQL?

**Benefits:**
- Automatic time-based partitioning
- Optimized time-series queries (10-100x faster)
- Built-in compression (90%+ space savings)
- Continuous aggregates for pre-computed summaries
- Familiar SQL interface
- Easy migration from PostgreSQL

**Use cases in Investment Lab:**
- Storing historical price data
- Query patterns like "get all prices for symbol X between dates Y and Z"
- Aggregations like "daily average price"

---

### Why Celery for background tasks?

**Benefits:**
- Battle-tested in production
- Easy integration with FastAPI
- Distributed task execution
- Automatic retry logic
- Task result storage
- Monitoring with Flower

**Alternatives considered:**
- `asyncio.create_task()` - Not persistent across restarts
- RQ (Redis Queue) - Simpler but less feature-rich
- Dramatiq - Good alternative, but smaller ecosystem

**Use case:** Long-running forecasts (1M+ paths) that would timeout HTTP requests

---

### Why lightweight-charts over Plotly for price charts?

**Benefits:**
- Much better performance (60 FPS with 100k data points)
- Smaller bundle size (~200KB vs 3MB+)
- TradingView look and feel
- Built for financial data
- Native WebSocket support
- Touch-friendly mobile interactions

**Trade-off:** Less flexibility than Plotly, but perfect for our use case

**Note:** We still use Plotly/Recharts for distribution plots where interactivity is more important than real-time performance

---

### GPU vs CPU for Monte Carlo?

**Performance comparison (10k paths, 252 steps):**

| Model | CPU (NumPy) | GPU (PyTorch) | Speedup |
|-------|-------------|---------------|---------|
| GBM   | ~500ms      | ~50ms         | 10x     |
| Heston| ~2000ms     | ~200ms        | 10x     |

**Scaling (GBM, 252 steps):**

| Paths | CPU      | GPU      | Speedup |
|-------|----------|----------|---------|
| 1k    | 50ms     | 20ms     | 2.5x    |
| 10k   | 500ms    | 50ms     | 10x     |
| 100k  | 5000ms   | 200ms    | 25x     |
| 1M    | 50000ms  | 1500ms   | 33x     |

**Conclusion:** GPU is essential for responsive UX with large simulations

---

### Why PyTorch over CuPy/Numba?

**PyTorch advantages:**
- Automatic differentiation (useful for calibration via gradient descent)
- Mature ecosystem
- Easy tensor operations
- Good memory management
- Future: Can integrate ML models seamlessly

**CuPy/Numba advantages:**
- Closer to NumPy API
- Slightly less overhead

**Decision:** PyTorch for consistency with potential ML features

---

### Monorepo vs Multi-repo?

**Recommendation: Monorepo**

**Benefits:**
- Atomic commits across frontend/backend
- Easier to coordinate API changes
- Shared types (via code generation or TypeScript in backend)
- Simplified CI/CD
- Single version control

**Structure:**
```
investment-lab/
├── backend/
├── frontend/
└── shared/ (optional)
```

---

## Testing Strategy

### Backend Testing

**Unit Tests (pytest):**
```python
# Test structure
tests/
├── unit/
│   ├── test_price_fetchers.py
│   ├── test_denomination_converter.py
│   ├── test_gbm_model.py
│   └── test_heston_model.py
├── integration/
│   ├── test_price_api.py
│   └── test_forecast_api.py
└── performance/
    └── test_monte_carlo.py
```

**Key test categories:**
1. **Fetcher tests** - Mock API responses, test error handling
2. **Converter tests** - Verify calculation accuracy
3. **Model tests** - Validate against known distributions
4. **API tests** - Test endpoints with TestClient
5. **WebSocket tests** - Connection handling, message flow

**Example test:**
```python
import pytest
import numpy as np
from scipy import stats

def test_gbm_distribution():
    """Verify GBM terminal distribution matches theory"""
    model = GBMModel(use_gpu=False)
    params = GBMParams(mu=0.05, sigma=0.2)
    S0 = 100
    T = 1.0
    
    # Run simulation
    terminal_prices = model.simulate(S0, T, params, n_paths=100000)
    
    # Theoretical distribution: log(S_T) ~ N(log(S0) + (μ - σ²/2)T, σ²T)
    theoretical_mean = S0 * np.exp(params.mu * T)
    log_prices = np.log(terminal_prices)
    
    # Chi-square goodness of fit test
    _, p_value = stats.normaltest(log_prices)
    assert p_value > 0.01  # Should be normally distributed
    
    # Mean should be close to theoretical
    assert abs(np.mean(terminal_prices) - theoretical_mean) / theoretical_mean < 0.01
```

**Coverage target:** >80% overall, >90% for core models

---

### Frontend Testing

**Unit Tests (Vitest + Testing Library):**
```typescript
// Example component test
import { render, screen, fireEvent } from '@testing-library/react';
import { AssetSelector } from './AssetSelector';

test('filters assets by search term', async () => {
  render(<AssetSelector onSelect={jest.fn()} />);
  
  const searchInput = screen.getByPlaceholderText('Search assets...');
  fireEvent.change(searchInput, { target: { value: 'AAPL' } });
  
  expect(await screen.findByText('Apple Inc.')).toBeInTheDocument();
  expect(screen.queryByText('Microsoft')).not.toBeInTheDocument();
});
```

**E2E Tests (Playwright):**
```typescript
// Example E2E test
import { test, expect } from '@playwright/test';

test('complete forecast workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Select asset
  await page.fill('[data-testid="asset-search"]', 'AAPL');
  await page.click('text=Apple Inc.');
  
  // Configure forecast
  await page.click('[data-testid="forecast-tab"]');
  await page.selectOption('[data-testid="model-select"]', 'gbm');
  await page.fill('[data-testid="horizon-input"]', '30');
  
  // Submit and wait for results
  await page.click('[data-testid="run-forecast"]');
  await expect(page.locator('[data-testid="distribution-chart"]')).toBeVisible({ timeout: 10000 });
});
```

---

### Performance Testing

**Load testing with Locust:**
```python
from locust import HttpUser, task, between

class InvestmentLabUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_price(self):
        self.client.get("/api/price/AAPL/in/BTC")
    
    @task(1)
    def run_forecast(self):
        self.client.post("/api/forecast/gbm", json={
            "symbol": "AAPL",
            "horizon_days": 30,
            "n_paths": 1000
        })
```

**Benchmarking:**
- Use `pytest-benchmark` for Python
- Use `console.time()` and Performance API for frontend
- Track metrics over time in CI

---

## Performance Targets

### Backend Performance

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Price fetch (cached) | < 50ms | p95 latency |
| Price fetch (uncached) | < 500ms | p95 latency |
| Denomination conversion | < 50ms | p95 latency |
| Historical data (1 year) | < 200ms | p95 latency |
| GBM forecast (10k paths) | < 1s | p95 on GPU |
| GBM forecast (100k paths) | < 5s | p95 on GPU |
| Heston forecast (10k paths) | < 3s | p95 on GPU |
| WebSocket message latency | < 100ms | p95 |

### Frontend Performance

| Metric | Target | Tool |
|--------|--------|------|
| First Contentful Paint | < 1.5s | Lighthouse |
| Time to Interactive | < 3s | Lighthouse |
| Chart render (1k points) | < 100ms | Performance API |
| Chart update (real-time) | 60 FPS | RequestAnimationFrame |
| Bundle size | < 500KB (gzipped) | webpack-bundle-analyzer |

### Database Performance

| Query Type | Target | Notes |
|------------|--------|-------|
| Single price lookup | < 10ms | Indexed by (symbol, timestamp) |
| Range query (1 year) | < 50ms | TimescaleDB optimization |
| Aggregation (daily avg) | < 100ms | Continuous aggregates |

---

## Future Features

### 1. Portfolio Analysis
- **Timeline:** Weeks 16-20
- **Complexity:** High
- **Dependencies:** Phase 3 complete

### 2. Options Pricing
- **Timeline:** Weeks 20-24
- **Complexity:** Very High
- **Dependencies:** Phase 3 complete

### 3. Machine Learning
- **Timeline:** Weeks 24-32
- **Complexity:** Very High
- **Dependencies:** Phase 3 complete, significant data collection

### 4. Backtesting Engine
- **Timeline:** Weeks 32-38
- **Complexity:** Very High
- **Dependencies:** Portfolio analysis complete

### 5. Alert System
- **Timeline:** Weeks 38-41
- **Complexity:** Medium
- **Dependencies:** Phase 2 complete

### 6. Advanced Models
- **Timeline:** Weeks 41-48
- **Complexity:** Very High
- **Dependencies:** Phase 3 complete

### 7. Social Features
- **Timeline:** Weeks 48+
- **Complexity:** Medium-High
- **Dependencies:** User authentication system

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.13
- Node.js 18+
- CUDA-capable GPU (optional but recommended)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/investment-lab.git
cd investment-lab

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start services
docker-compose up -d

# Install backend dependencies
cd backend
poetry install  # or: uv sync

# Install frontend dependencies
cd frontend
npm install

# Run migrations
cd backend
alembic upgrade head

# Access application
# API: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## Current Status

- [x] Planning & Design
- [ ] Phase 1: Foundation
- [ ] Phase 2: Denominational Pricing
- [ ] Phase 3: Forecasting
- [ ] Phase 4: Optimization
- [ ] Phase 5: Advanced Features

---

## Notes

- This is a living document - update as implementation progresses
- Add links to relevant documentation and code as features are completed
- Track technical debt and improvements needed
- Document lessons learned and architectural decisions

---

**Last Updated:** November 7, 2025  
**Next Review:** After Phase 1 completion