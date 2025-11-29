# Investment Lab

A financial analysis platform for real-time asset pricing, multi-currency conversions, and GPU-accelerated stochastic forecasting.

## Features

### Price Data & Analysis
- **Real-time pricing** for stocks, ETFs, and cryptocurrencies
- **Multi-currency support** - View prices in USD, GBP, EUR, BTC, ETH, and more
- **Historical data** with interactive charts
- **Cross-asset pricing** - See any asset priced in any denomination (e.g., AAPL in BTC)

### Stochastic Forecasting
- **Monte Carlo simulations** using Geometric Brownian Motion (GBM)
- **GPU acceleration** with PyTorch for 100K-1M+ simulation paths
- **Customizable horizons** - Forecast 1 day to 10 years ahead
- **Risk metrics** - VaR, CVaR, confidence intervals, and probability distributions
- **Interactive visualizations** - Distribution charts, confidence bands, sample paths

## Tech Stack

**Backend:**
- Python 3.13+ with FastAPI
- PyTorch (GPU-accelerated forecasting)
- yfinance & Alpha Vantage (market data)
- Pydantic for data validation

**Frontend:**
- React + TypeScript
- Vite build system
- TailwindCSS + Recharts
- React Query for state management

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- (Optional) CUDA-capable GPU for faster forecasting

### Backend Setup

```bash
cd backend

# Install dependencies
poetry install
# or: uv sync

# Set up environment (optional - works without API keys using yfinance)
cp .env.example .env
# Add your Alpha Vantage API key if desired

# Run the API server
poetry run uvicorn src.api.main:app --reload
# API will be available at http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# App will be available at http://localhost:5173
```

### Docker (Full Stack)

```bash
# Start both backend and frontend
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Project Structure

```
investment-lab/
├── backend/              # Python FastAPI backend
│   ├── src/
│   │   ├── api/         # REST API endpoints
│   │   ├── price_service/    # Price fetching & conversions
│   │   ├── forecast_service/ # Monte Carlo models
│   │   └── core/        # Configuration & utilities
│   └── tests/           # Test suite
│
├── frontend/            # React TypeScript frontend
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Route pages
│       ├── api/         # API client & hooks
│       └── utils/       # Helpers & formatters
│
└── docs/                # Documentation
    ├── QUICKSTART.md    # Detailed setup guide
    ├── GBM-basic.md     # Forecasting model docs
    └── ...              # Additional technical docs
```

## Usage Examples

### Fetch Asset Prices

```python
from price_service.fetchers import YFinanceFetcher
from price_service.models import AssetType

fetcher = YFinanceFetcher()

# Stock price
aapl = await fetcher.fetch_price("AAPL", AssetType.STOCK)
print(f"Apple: ${aapl.price}")

# Cryptocurrency
btc = await fetcher.fetch_price("BTC-USD", AssetType.CRYPTO)
print(f"Bitcoin: ${btc.price:,.2f}")
```

### Generate Forecast

```python
from forecast_service.models.gbm import GBMModel

model = GBMModel(use_gpu=True)

# Run 100K Monte Carlo paths
forecast = model.forecast(
    params=calibrated_params,
    horizon_days=30,
    n_paths=100000
)

print(f"Expected price: ${forecast['mean']:.2f}")
print(f"95% confidence: ${forecast['percentiles']['p95']:.2f}")
```

## API Endpoints

- `GET /api/price/{symbol}` - Get current price
- `GET /api/historical/{symbol}` - Historical data
- `POST /api/convert` - Cross-currency conversion
- `POST /api/forecast/gbm` - Generate forecast

**API Documentation:** http://localhost:8000/docs

## Configuration

### Forecast Defaults
- **Simulation paths:** 10K-1M (default: 10K)
- **Sample paths:** 500 (for visualization)
- **Horizon:** 1-3,650 days (default: 30)
- **Calibration period:** 252 trading days (1 year)

### Supported Assets
- **Stocks & ETFs:** AAPL, MSFT, SPY, QQQ, etc.
- **Cryptocurrencies:** BTC, ETH, SOL, etc.
- **Fiat currencies:** USD, GBP, EUR, JPY

## Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Detailed setup and usage guide
- **[FRONTEND.md](FRONTEND.md)** - Frontend architecture and components
- **[Backend README](backend/README.MD)** - Backend API details
- **[GBM Forecasting](docs/GBM-basic.md)** - Model documentation
- **[API Docs](http://localhost:8000/docs)** - Interactive API reference (when running)

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Quality

```bash
# Backend
ruff check src
mypy src

# Frontend
npm run lint
npm run type-check
```

## Key Features in Detail

### GPU Acceleration
The forecasting engine uses PyTorch to leverage GPU acceleration for Monte Carlo simulations, enabling 100K-1M+ paths in seconds instead of minutes.

### Dynamic Currency Symbols
Prices are displayed with the correct currency symbol based on the asset:
- `AAPL` → `$175.50` (USD)
- `BTC-GBP` → `£45,230.00` (GBP)
- `ETH-EUR` → `€2,340.50` (EUR)

### Custom Forecast Parameters
Users can customize both the number of simulation paths (100-10M) and forecast horizon (1 day to 10 years) for flexibility across different use cases.

## License

MIT

## Contributing

See the [ROADMAP](Research/ROADMAP.md) for planned features and contribution areas.
