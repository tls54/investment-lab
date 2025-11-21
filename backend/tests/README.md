# Tests

Unit tests for the Investment Lab backend.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

## Test Structure

```
tests/
├── conftest.py                  # Pytest fixtures and configuration
├── test_models.py               # Tests for data models (Price, HistoricalPrice)
├── test_base_fetcher.py         # Tests for base fetcher logic (caching, rate limiting)
└── test_crypto_currencies.py    # Tests for multi-currency crypto pricing
```

## What's Tested

### ✅ `test_models.py`
- Price model validation
- Symbol/currency normalization
- Negative price rejection
- Optional fields
- HistoricalPrice sorting
- Custom exceptions

### ✅ `test_base_fetcher.py`
- Rate limiting enforcement
- Cache operations (set, get, expiration)
- Asset type support checking
- Abstract base class requirements

### ⚠️ `test_crypto_currencies.py` (Integration Tests)
**Note:** These tests require network access to yfinance API.

Tests covered:
- Current price in multiple currencies (USD, EUR, GBP, JPY, AUD, CAD)
- Default currency behavior (USD)
- Unsupported currency error handling
- Case-insensitive currency codes
- Historical data with custom currencies
- Currency validation and edge cases
- Documentation of known supported currencies
- Placeholder tests for future triangular conversion feature

**Run currency tests:**
```bash
# Run all currency tests
pytest tests/test_crypto_currencies.py -v

# Run only tests for known supported currencies
pytest tests/test_crypto_currencies.py::TestCryptoCurrentPrice::test_supported_currencies -v

# Skip tests that require network
pytest -m "not integration"
```

### ❌ Not Tested (External APIs)
- Alpha Vantage integration (manual testing)

### 🔜 Future Tests (Marked as Skip)
- Triangular currency conversion (BTC-INR via BTC-USD × USD-INR)

## Test Coverage

Run `pytest --cov=src --cov-report=html` to see coverage report.

Current coverage targets:
- Models: ~95%
- Base fetcher: ~90%
- API integrations: Manual testing only