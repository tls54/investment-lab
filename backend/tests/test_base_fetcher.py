"""Unit tests for base fetcher functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from price_service.models import AssetType, Price, RateLimitError
from price_service.fetchers.base import AssetFetcher, BaseFetcherWithCache


class MockFetcher(AssetFetcher):
    """Mock fetcher for testing base class functionality."""
    
    @property
    def name(self) -> str:
        return "Mock Fetcher"
    
    @property
    def supported_asset_types(self) -> list[AssetType]:
        return [AssetType.STOCK, AssetType.CRYPTO]
    
    async def fetch_price(self, symbol: str, asset_type: AssetType | None = None) -> Price:
        return Price(
            symbol=symbol,
            asset_type=asset_type or AssetType.STOCK,
            price=100.0,
            timestamp=datetime.now(),
            source=self.name
        )
    
    async def fetch_historical(self, symbol: str, start: datetime, end: datetime,
                              interval: str = "1d", asset_type: AssetType | None = None):
        pass
    
    async def validate_symbol(self, symbol: str, asset_type: AssetType | None = None) -> bool:
        return symbol != "INVALID"


class TestAssetFetcher:
    """Tests for AssetFetcher base class."""
    
    def test_initialization(self):
        """Test fetcher initialization."""
        fetcher = MockFetcher(api_key="test_key", rate_limit_per_minute=5)
        
        assert fetcher.api_key == "test_key"
        assert fetcher.rate_limit_per_minute == 5
        assert fetcher._call_count == 0
    
    def test_supports_asset_type(self):
        """Test asset type support checking."""
        fetcher = MockFetcher()
        
        assert fetcher.supports_asset_type(AssetType.STOCK) is True
        assert fetcher.supports_asset_type(AssetType.CRYPTO) is True
        assert fetcher.supports_asset_type(AssetType.COMMODITY) is False
        assert fetcher.supports_asset_type(AssetType.FOREX) is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced."""
        fetcher = MockFetcher(rate_limit_per_minute=2)
        
        # First two calls should succeed
        await fetcher._check_rate_limit()
        await fetcher._check_rate_limit()
        
        # Third call should raise RateLimitError
        with pytest.raises(RateLimitError) as exc_info:
            await fetcher._check_rate_limit()
        
        assert exc_info.value.source == "Mock Fetcher"
        assert exc_info.value.retry_after is not None
    
    @pytest.mark.asyncio
    async def test_no_rate_limit_when_none(self):
        """Test that no rate limiting occurs when limit is None."""
        fetcher = MockFetcher(rate_limit_per_minute=None)
        
        # Should be able to call many times without error
        for _ in range(100):
            await fetcher._check_rate_limit()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager support."""
        async with MockFetcher() as fetcher:
            assert fetcher is not None
            assert isinstance(fetcher, MockFetcher)


class TestBaseFetcherWithCache:
    """Tests for BaseFetcherWithCache."""
    
    class MockCachedFetcher(BaseFetcherWithCache):
        """Mock cached fetcher for testing."""
        
        @property
        def name(self) -> str:
            return "Mock Cached Fetcher"
        
        @property
        def supported_asset_types(self) -> list[AssetType]:
            return [AssetType.STOCK]
        
        async def fetch_price(self, symbol: str, asset_type: AssetType | None = None) -> Price:
            return Price(
                symbol=symbol,
                asset_type=asset_type or AssetType.STOCK,
                price=100.0,
                timestamp=datetime.now(),
                source=self.name
            )
        
        async def fetch_historical(self, symbol: str, start: datetime, end: datetime,
                                  interval: str = "1d", asset_type: AssetType | None = None):
            pass
        
        async def validate_symbol(self, symbol: str, asset_type: AssetType | None = None) -> bool:
            return True
    
    def test_cache_initialization(self):
        """Test cache initialization."""
        fetcher = self.MockCachedFetcher(cache_ttl_seconds=60)
        
        assert fetcher.cache_ttl_seconds == 60
        assert len(fetcher._cache) == 0
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        fetcher = self.MockCachedFetcher()
        
        key1 = fetcher._get_cache_key("AAPL", "stock")
        key2 = fetcher._get_cache_key("AAPL", "stock")
        key3 = fetcher._get_cache_key("MSFT", "stock")
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different inputs = different key
    
    def test_cache_set_and_get(self):
        """Test setting and getting from cache."""
        fetcher = self.MockCachedFetcher(cache_ttl_seconds=60)
        
        key = "test_key"
        value = {"price": 100.0}
        
        # Set in cache
        fetcher._set_in_cache(key, value)
        
        # Get from cache
        cached_value = fetcher._get_from_cache(key)
        
        assert cached_value == value
    
    def test_cache_expiration(self):
        """Test that cache entries expire."""
        import time
        
        fetcher = self.MockCachedFetcher(cache_ttl_seconds=1)  # 1 second TTL
        
        key = "test_key"
        value = {"price": 100.0}
        
        # Set in cache
        fetcher._set_in_cache(key, value)
        
        # Should be in cache
        assert fetcher._get_from_cache(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert fetcher._get_from_cache(key) is None
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        fetcher = self.MockCachedFetcher()
        
        value = fetcher._get_from_cache("nonexistent_key")
        
        assert value is None


class TestFetcherInterface:
    """Tests to ensure all required methods are abstract."""
    
    def test_cannot_instantiate_base_fetcher(self):
        """Test that AssetFetcher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AssetFetcher()
    
    def test_subclass_must_implement_all_methods(self):
        """Test that subclasses must implement all abstract methods."""
        
        class IncompleteFetcher(AssetFetcher):
            @property
            def name(self) -> str:
                return "Incomplete"
            
            # Missing: supported_asset_types, fetch_price, fetch_historical, validate_symbol
        
        with pytest.raises(TypeError):
            IncompleteFetcher()