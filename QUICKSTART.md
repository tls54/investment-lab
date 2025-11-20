# Investment Lab - Quick Start Guide

## What We've Built

We've implemented the **core price fetching system** for Investment Lab:

✅ **Data Models** - Pydantic models for Price and HistoricalPrice
✅ **Base Fetcher** - Abstract class with caching and rate limiting
✅ **Alpha Vantage Client** - Stocks, ETFs, commodities, forex
✅ **yfinance Client** - Stocks, ETFs, and cryptocurrencies (free, no API key)
✅ **Test Suite** - Comprehensive test script  

## Project Structure

```
investment-lab/backend/
├── src/
│   ├── price_service/
│   │   ├── models.py              # Pydantic data models
│   │   ├── fetchers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Abstract base class
│   │   │   ├── alpha_vantage.py   # Stock/commodity fetcher
│   │   │   └── yfinance_fetcher.py # Stock/ETF/crypto fetcher
│   │   └── __init__.py
│   ├── test_fetchers.py           # Test script
│   └── __init__.py
├── pyproject.toml                 # Dependencies
└── README.md
```

## Getting Started (5 Minutes)

### Step 1: Install Dependencies

```bash
cd investment-lab/backend

# Option A: Using Poetry (recommended)
poetry install

# Option B: Using pip
pip install httpx pydantic

# For full functionality (forecasting, etc.)
pip install httpx pydantic fastapi uvicorn redis torch numpy pandas scipy
```

### Step 2: Get API Keys

**Alpha Vantage** (optional for stocks):
1. Visit https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Get your free API key instantly
4. Free tier: 500 calls/day, 5 calls/minute

**yfinance** (no key needed):
- Works without an API key
- No rate limits
- Supports stocks, ETFs, and cryptocurrencies

### Step 3: Set Environment Variables

```bash
# Linux/Mac
export ALPHA_VANTAGE_API_KEY="your_key_here"

# Windows (PowerShell)
$env:ALPHA_VANTAGE_API_KEY="your_key_here"

# Windows (CMD)
set ALPHA_VANTAGE_API_KEY=your_key_here
```

### Step 4: Run Tests

```bash
# If using Poetry
poetry run python -m src.test_fetchers

# If using pip
python -m src.test_fetchers
```

You should see output like:

```
============================================================
Investment Lab - Fetcher Test Suite
============================================================

============================================================
Testing Alpha Vantage Fetcher
============================================================

Test 1: Fetching current price for IBM...
✓ Success!
  Symbol: IBM
  Price: $175.50
  Timestamp: 2025-11-07 10:30:00
  Volume: 3,450,000
  Source: Alpha Vantage

[... more test output ...]
```

## Usage Examples

### Example 1: Fetch Stock Price

```python
import asyncio
from price_service.fetchers import AlphaVantageFetcher
from price_service.models import AssetType

async def main():
    fetcher = AlphaVantageFetcher(api_key="your_key")
    
    # Get current price
    price = await fetcher.fetch_price("AAPL", AssetType.STOCK)
    print(f"Apple stock: ${price.price}")
    print(f"Volume: {price.volume:,}")

asyncio.run(main())
```

### Example 2: Fetch Crypto Price

```python
import asyncio
from price_service.fetchers import YFinanceFetcher
from price_service.models import AssetType

async def main():
    fetcher = YFinanceFetcher()

    # Bitcoin (automatically appends -USD for yfinance)
    btc = await fetcher.fetch_price("BTC", AssetType.CRYPTO)
    print(f"Bitcoin: ${btc.price:,.2f}")

    # Ethereum
    eth = await fetcher.fetch_price("ETH", AssetType.CRYPTO)
    print(f"Ethereum: ${eth.price:,.2f}")

asyncio.run(main())
```

### Example 3: Historical Data

```python
import asyncio
from datetime import datetime, timedelta
from price_service.fetchers import YFinanceFetcher
from price_service.models import AssetType

async def main():
    fetcher = YFinanceFetcher()

    # Last 7 days of Bitcoin prices
    end = datetime.now()
    start = end - timedelta(days=7)

    historical = await fetcher.fetch_historical("BTC", start, end, asset_type=AssetType.CRYPTO)

    print(f"Got {len(historical.prices)} data points")
    for price in historical.prices:
        print(f"{price.timestamp.date()}: ${price.price:,.2f}")

asyncio.run(main())
```

### Example 4: Multiple Assets

```python
import asyncio
from price_service.fetchers import YFinanceFetcher
from price_service.models import AssetType

async def get_portfolio_value():
    fetcher = YFinanceFetcher()

    # Holdings
    holdings = {
        "AAPL": 10,      # 10 shares
        "MSFT": 5,       # 5 shares
        "BTC": 0.5,      # 0.5 Bitcoin
        "ETH": 2,        # 2 Ethereum
    }

    # Fetch prices (yfinance handles both stocks and crypto)
    aapl = await fetcher.fetch_price("AAPL", AssetType.STOCK)
    msft = await fetcher.fetch_price("MSFT", AssetType.STOCK)
    btc = await fetcher.fetch_price("BTC", AssetType.CRYPTO)
    eth = await fetcher.fetch_price("ETH", AssetType.CRYPTO)

    # Calculate total
    total = (
        holdings["AAPL"] * aapl.price +
        holdings["MSFT"] * msft.price +
        holdings["BTC"] * btc.price +
        holdings["ETH"] * eth.price
    )

    print(f"Portfolio Value: ${total:,.2f}")

asyncio.run(get_portfolio_value())
```

## Key Features

### Automatic Caching
Fetchers with caching support reduce API calls:
```python
from price_service.fetchers import AlphaVantageFetcher

fetcher = AlphaVantageFetcher(api_key="your_key", cache_ttl_seconds=60)

# First call hits the API
price1 = await fetcher.fetch_price("AAPL")  # ~200ms

# Second call uses cache
price2 = await fetcher.fetch_price("AAPL")  # ~0.1ms (2000x faster!)
```

### Rate Limiting
Automatic rate limit handling:
```python
fetcher = AlphaVantageFetcher(
    api_key="your_key",
    rate_limit_per_minute=5  # Enforces 5 calls/minute
)

# Automatically waits if rate limit exceeded
# Raises RateLimitError with retry_after time
```

### Error Handling
```python
from price_service.models import SymbolNotFoundError, RateLimitError, APIError

try:
    price = await fetcher.fetch_price("INVALID_SYMBOL")
except SymbolNotFoundError as e:
    print(f"Symbol not found: {e.symbol}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except APIError as e:
    print(f"API error: {e.message}")
```

### Data Validation
All data is validated using Pydantic:
```python
# This will raise ValidationError if price is negative
price = Price(
    symbol="AAPL",
    asset_type=AssetType.STOCK,
    price=-100,  # ❌ Invalid! Must be positive
    timestamp=datetime.now(),
    source="test"
)
```

## Next Steps

Now that the fetchers are working, we can:

1. ✅ **Add yfinance fallback** - Backup data source for stocks
2. ✅ **Build FastAPI endpoints** - REST API for price data
3. ✅ **Add Redis caching** - Shared cache across instances
4. ✅ **Implement WebSockets** - Real-time price streaming
5. ✅ **Create denomination converter** - AAPL priced in BTC, etc.

## Troubleshooting

### "ModuleNotFoundError: No module named 'httpx'"
```bash
pip install httpx pydantic
```

### "No API key" error
Make sure you've set the environment variable:
```bash
export ALPHA_VANTAGE_API_KEY="your_key_here"
```

### Rate limit errors
Use the demo key with symbol "IBM" or wait for the rate limit to reset (60 seconds).

### Crypto symbol not found
For cryptocurrencies with yfinance, use the base symbol (e.g., BTC, ETH).
Common crypto symbols:
- BTC, ETH, USDT, BNB, SOL, USDC, XRP, DOGE, ADA, etc.

The system automatically appends -USD for yfinance compatibility.

## Testing Without API Keys

You can test yfinance without any API key:
```bash
python -c "
import asyncio
from src.price_service.fetchers import YFinanceFetcher
from src.price_service.models import AssetType

async def test():
    fetcher = YFinanceFetcher()
    btc = await fetcher.fetch_price('BTC', AssetType.CRYPTO)
    print(f'BTC: ${btc.price:,.2f}')

asyncio.run(test())
"
```

For Alpha Vantage, use the demo key with "IBM":
```bash
export ALPHA_VANTAGE_API_KEY="demo"
python -m src.test_fetchers
```

## Documentation

- **Alpha Vantage API**: https://www.alphavantage.co/documentation/
- **yfinance**: https://github.com/ranaroussi/yfinance
- **Pydantic Docs**: https://docs.pydantic.dev/

## Questions?

Refer to the full [ROADMAP.md](ROADMAP.md) for the complete project plan!