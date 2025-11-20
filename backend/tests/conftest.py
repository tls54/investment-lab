"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_symbol():
    """Sample stock symbol for testing."""
    return "AAPL"


@pytest.fixture
def sample_crypto_symbol():
    """Sample crypto symbol for testing."""
    return "BTC"


@pytest.fixture
def date_range():
    """Sample date range for historical data tests."""
    end = datetime.now()
    start = end - timedelta(days=7)
    return start, end


@pytest.fixture
def mock_price_data():
    """Mock price data for testing."""
    return {
        "symbol": "AAPL",
        "price": 175.50,
        "timestamp": datetime.now(),
        "volume": 50000000,
        "source": "test"
    }