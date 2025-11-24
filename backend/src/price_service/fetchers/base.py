"""
Base class for all asset price fetchers.

This module defines the interface that all data source fetchers must implement.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
import logging

from ..models import Price, HistoricalPrice, AssetType


logger = logging.getLogger(__name__)


class AssetFetcher(ABC):
    """
    Abstract base class for fetching asset prices from various data sources.
    
    All concrete fetcher implementations must inherit from this class and
    implement the required methods.
    
    Attributes:
        name: Human-readable name of the data source
        rate_limit_per_minute: Maximum API calls per minute (None for unlimited)
        supports_real_time: Whether this source provides real-time data
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_per_minute: Optional[int] = None
    ):
        """
        Initialize the fetcher.
        
        Args:
            api_key: API key for the data source (if required)
            rate_limit_per_minute: Override default rate limit
        """
        self.api_key = api_key
        self.rate_limit_per_minute = rate_limit_per_minute
        self._call_count = 0
        self._last_reset = datetime.now()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this data source."""
        pass
    
    @property
    @abstractmethod
    def supported_asset_types(self) -> List[AssetType]:
        """Return list of asset types this fetcher supports."""
        pass
    
    @abstractmethod
    async def fetch_price(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None,
        currency: str = "USD"
    ) -> Price:
        """
        Fetch the current price for a given symbol.

        Args:
            symbol: Asset symbol (e.g., "AAPL", "BTC", "GC")
            asset_type: Type of asset (auto-detect if None)
            currency: Currency for the price (e.g., "USD", "EUR", "GBP")

        Returns:
            Price object with current price data

        Raises:
            SymbolNotFoundError: If symbol is not found
            RateLimitError: If rate limit is exceeded
            APIError: If API returns an error
        """
        pass
    
    @abstractmethod
    async def fetch_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        asset_type: Optional[AssetType] = None,
        currency: str = "USD"
    ) -> HistoricalPrice:
        """
        Fetch historical prices for a given symbol.

        Args:
            symbol: Asset symbol
            start: Start date for historical data
            end: End date for historical data
            interval: Time interval (e.g., "1d", "1h", "5m")
            asset_type: Type of asset (auto-detect if None)
            currency: Currency for the price (e.g., "USD", "EUR", "GBP")

        Returns:
            HistoricalPrice object with price series

        Raises:
            SymbolNotFoundError: If symbol is not found
            RateLimitError: If rate limit is exceeded
            APIError: If API returns an error
        """
        pass
    
    @abstractmethod
    async def validate_symbol(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None
    ) -> bool:
        """
        Check if a symbol is valid for this data source.
        
        Args:
            symbol: Asset symbol to validate
            asset_type: Type of asset (auto-detect if None)
            
        Returns:
            True if symbol is valid, False otherwise
        """
        pass
    
    def supports_asset_type(self, asset_type: AssetType) -> bool:
        """
        Check if this fetcher supports a given asset type.
        
        Args:
            asset_type: Asset type to check
            
        Returns:
            True if supported, False otherwise
        """
        return asset_type in self.supported_asset_types
    
    async def _check_rate_limit(self) -> None:
        """
        Check if we're within rate limits.
        
        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        if self.rate_limit_per_minute is None:
            return
        
        now = datetime.now()
        elapsed = (now - self._last_reset).total_seconds()
        
        # Reset counter every minute
        if elapsed >= 60:
            self._call_count = 0
            self._last_reset = now
        
        if self._call_count >= self.rate_limit_per_minute:
            retry_after = int(60 - elapsed)
            logger.warning(
                f"Rate limit exceeded for {self.name}. "
                f"Retry after {retry_after} seconds"
            )
            from ..models import RateLimitError
            raise RateLimitError(self.name, retry_after)
        
        self._call_count += 1
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cleanup can be implemented by subclasses if needed
        pass


class BaseFetcherWithCache(AssetFetcher):
    """
    Base fetcher with simple in-memory caching.
    
    This is a basic implementation. In production, we'll use Redis.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_per_minute: Optional[int] = None,
        cache_ttl_seconds: int = 60
    ):
        super().__init__(api_key, rate_limit_per_minute)
        self._cache = {}
        self.cache_ttl_seconds = cache_ttl_seconds
    
    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        return ":".join(str(arg) for arg in args)
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        age = (datetime.now() - timestamp).total_seconds()
        
        if age > self.cache_ttl_seconds:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return value
    
    def _set_in_cache(self, key: str, value: any) -> None:
        """Store value in cache with timestamp."""
        self._cache[key] = (value, datetime.now())
        logger.debug(f"Cached value for key: {key}")