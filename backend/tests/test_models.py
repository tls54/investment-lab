"""Unit tests for price_service models."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from price_service.models import (
    Price,
    HistoricalPrice,
    AssetType,
    SymbolNotFoundError,
    RateLimitError,
    APIError
)


class TestPrice:
    """Tests for Price model."""
    
    def test_valid_price_creation(self):
        """Test creating a valid Price object."""
        price = Price(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            price=175.50,
            timestamp=datetime.now(),
            currency="USD",
            volume=50000000,
            source="test"
        )
        
        assert price.symbol == "AAPL"
        assert price.price == 175.50
        assert price.asset_type == AssetType.STOCK
        assert price.currency == "USD"
    
    def test_symbol_normalization(self):
        """Test that symbols are normalized to uppercase."""
        price = Price(
            symbol="aapl",  # lowercase
            asset_type=AssetType.STOCK,
            price=175.50,
            timestamp=datetime.now(),
            source="test"
        )
        
        assert price.symbol == "AAPL"  # Should be uppercase
    
    def test_currency_normalization(self):
        """Test that currency codes are normalized to uppercase."""
        price = Price(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            price=175.50,
            timestamp=datetime.now(),
            currency="usd",  # lowercase
            source="test"
        )
        
        assert price.currency == "USD"  # Should be uppercase
    
    def test_negative_price_rejected(self):
        """Test that negative prices are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=-100.0,  # Invalid: negative
                timestamp=datetime.now(),
                source="test"
            )
        
        assert "price" in str(exc_info.value).lower()
    
    def test_zero_price_rejected(self):
        """Test that zero prices are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=0.0,  # Invalid: zero
                timestamp=datetime.now(),
                source="test"
            )
        
        assert "price" in str(exc_info.value).lower()
    
    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        price = Price(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            price=175.50,
            timestamp=datetime.now(),
            source="test",
            # Optional fields
            bid=175.45,
            ask=175.55,
            high_24h=176.00,
            low_24h=174.50
        )
        
        assert price.bid == 175.45
        assert price.ask == 175.55
        assert price.high_24h == 176.00
        assert price.low_24h == 174.50


class TestHistoricalPrice:
    """Tests for HistoricalPrice model."""
    
    def test_valid_historical_creation(self):
        """Test creating a valid HistoricalPrice object."""
        now = datetime.now()
        prices = [
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=175.50,
                timestamp=now,
                source="test"
            )
        ]
        
        historical = HistoricalPrice(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            prices=prices,
            start_date=now,
            end_date=now,
            interval="1d"
        )
        
        assert historical.symbol == "AAPL"
        assert len(historical.prices) == 1
        assert historical.interval == "1d"
    
    def test_prices_sorted_by_timestamp(self):
        """Test that prices are automatically sorted by timestamp."""
        now = datetime.now()
        
        # Create prices in reverse order
        prices = [
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=175.50,
                timestamp=now,
                source="test"
            ),
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=174.50,
                timestamp=now - timedelta(days=1),
                source="test"
            ),
            Price(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                price=173.50,
                timestamp=now - timedelta(days=2),
                source="test"
            )
        ]
        
        historical = HistoricalPrice(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            prices=prices,
            start_date=now - timedelta(days=2),
            end_date=now,
            interval="1d"
        )
        
        # Should be sorted oldest to newest
        assert historical.prices[0].price == 173.50
        assert historical.prices[1].price == 174.50
        assert historical.prices[2].price == 175.50
    
    def test_empty_prices_rejected(self):
        """Test that empty price lists are rejected."""
        now = datetime.now()
        
        with pytest.raises(ValidationError) as exc_info:
            HistoricalPrice(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                prices=[],  # Empty list
                start_date=now,
                end_date=now,
                interval="1d"
            )
        
        assert "prices" in str(exc_info.value).lower()


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_symbol_not_found_error(self):
        """Test SymbolNotFoundError."""
        error = SymbolNotFoundError("INVALID", "test_source")
        
        assert error.symbol == "INVALID"
        assert error.source == "test_source"
        assert "INVALID" in str(error)
        assert "test_source" in str(error)
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("test_source", retry_after=60)
        
        assert error.source == "test_source"
        assert error.retry_after == 60
        assert "test_source" in str(error)
        assert "60" in str(error)
    
    def test_rate_limit_error_without_retry(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError("test_source")
        
        assert error.source == "test_source"
        assert error.retry_after is None
    
    def test_api_error(self):
        """Test APIError."""
        error = APIError("test_source", 500, "Internal Server Error")
        
        assert error.source == "test_source"
        assert error.status_code == 500
        assert error.message == "Internal Server Error"
        assert "500" in str(error)


class TestAssetType:
    """Tests for AssetType enum."""
    
    def test_all_asset_types_exist(self):
        """Test that all expected asset types exist."""
        assert AssetType.STOCK == "stock"
        assert AssetType.CRYPTO == "crypto"
        assert AssetType.COMMODITY == "commodity"
        assert AssetType.FOREX == "forex"
        assert AssetType.ETF == "etf"
    
    def test_asset_type_in_price_model(self):
        """Test that AssetType works with Price model."""
        for asset_type in AssetType:
            price = Price(
                symbol="TEST",
                asset_type=asset_type,
                price=100.0,
                timestamp=datetime.now(),
                source="test"
            )
            assert price.asset_type == asset_type