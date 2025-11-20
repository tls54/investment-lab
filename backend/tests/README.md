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
├── conftest.py              # Pytest fixtures and configuration
├── test_models.py           # Tests for data models (Price, HistoricalPrice)
└── test_base_fetcher.py     # Tests for base fetcher logic (caching, rate limiting)
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

### ❌ Not Tested (External APIs)
- Alpha Vantage integration
- yfinance integration

These require network access, so we test them manually or with integration tests.

## Test Coverage

Run `pytest --cov=src --cov-report=html` to see coverage report.

Current coverage targets:
- Models: ~95%
- Base fetcher: ~90%
- API integrations: Manual testing only