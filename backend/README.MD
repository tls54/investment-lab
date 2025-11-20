# Investment Lab - Backend

Backend services for the Investment Lab financial analysis platform.

## Features

- **Price Fetching**: Real-time and historical price data from multiple sources
  - Alpha Vantage (stocks, commodities, forex)
  - yfinance (stocks, ETFs, cryptocurrencies - free, no API key)
- **Denominational Pricing**: Convert any asset price to any denomination
- **Stochastic Forecasting**: GBM and Heston models for price prediction
- **GPU Acceleration**: PyTorch-based Monte Carlo simulations

## Setup

### Prerequisites

- Python 3.13+
- Poetry or uv for dependency management
- (Optional) CUDA-capable GPU for forecasting

### Installation

1. **Install dependencies**:

Using Poetry:
```bash
cd backend
poetry install
```

Using uv:
```bash
cd backend
uv sync
```

2. **Set up environment variables**:

Create a `.env` file in the backend directory:

```bash
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here  # Get free key at https://www.alphavantage.co/support/#api-key

# Application
ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# Database (PostgreSQL/TimescaleDB)
DATABASE_URL=postgresql://user:password@localhost:5432/investment_lab

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### Testing the Fetchers

Run the test script to verify everything is working:

```bash
# Using Poetry
poetry run python -m src.test_fetchers

# Using uv
uv run python -m src.test_fetchers

# Or activate the virtual environment first
poetry shell  # or: source .venv/bin/activate
python -m src.test_fetchers
```

**Note**: The test script uses the "demo" API key for Alpha Vantage by default, which only works with the symbol "IBM". Set your real API key in the environment to test with other symbols.

## Project Structure

```
backend/
├── src/
│   ├── api/              # FastAPI routes and endpoints
│   ├── price_service/    # Price fetching and conversion
│   │   ├── fetchers/     # Data source implementations
│   │   │   ├── base.py
│   │   │   ├── alpha_vantage.py
│   │   │   └── yfinance_fetcher.py
│   │   └── models.py     # Pydantic data models
│   ├── forecast_service/ # Forecasting models (coming soon)
│   ├── core/             # Core utilities and config
│   └── tests/            # Test suite
├── pyproject.toml        # Dependencies and config
└── README.md
```

## Usage Examples

### Fetching Current Prices

```python
from price_service.fetchers import YFinanceFetcher
from price_service.models import AssetType

# Initialize fetcher (no API key needed)
fetcher = YFinanceFetcher()

# Stock price
price = await fetcher.fetch_price("AAPL", AssetType.STOCK)
print(f"AAPL: ${price.price}")

# Crypto price (automatically appends -USD for yfinance)
btc_price = await fetcher.fetch_price("BTC", AssetType.CRYPTO)
print(f"BTC: ${btc_price.price:,.2f}")
```

### Fetching Historical Data

```python
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

historical = await fetcher.fetch_historical(
    "AAPL",
    start_date,
    end_date,
    interval="1d",
    asset_type=AssetType.STOCK
)

print(f"Got {len(historical.prices)} data points")
for price in historical.prices[-5:]:  # Last 5 days
    print(f"{price.timestamp.date()}: ${price.price}")
```

## Data Sources

### yfinance

- **Supports**: Stocks, ETFs, Cryptocurrencies
- **Rate Limit**: None (free tier)
- **API Key**: Not required
- **Documentation**: https://github.com/ranaroussi/yfinance

### Alpha Vantage

- **Supports**: Stocks, ETFs, Commodities, Forex, Crypto
- **Rate Limit**: 5 calls/minute (free tier)
- **Documentation**: https://www.alphavantage.co/documentation/

## Development

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy src
```

### Linting

```bash
ruff check src
```

### Formatting

```bash
black src
```

## Next Steps

1. Add more data sources (yfinance fallback)
2. Implement Redis caching layer
3. Build FastAPI endpoints
4. Add authentication and rate limiting
5. Implement forecasting models

## API Documentation

Once the FastAPI server is running, visit:
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

See [ROADMAP.md](../../ROADMAP.md) for the full project plan and implementation phases.

## License

MIT