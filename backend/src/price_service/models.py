"""
Price data models for the Investment Lab.

These models define the structure for price data across all asset types.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AssetType(str, Enum):
    """Supported asset types."""
    STOCK = "stock"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    FOREX = "forex"
    ETF = "etf"


class Price(BaseModel):
    """
    Represents a single price observation for an asset.
    
    Attributes:
        symbol: Asset identifier (e.g., "AAPL", "BTC", "GC")
        asset_type: Type of asset
        price: Current price
        timestamp: When this price was observed
        currency: Base currency for the price (default: USD)
        volume: Trading volume (if available)
        source: Data source name (e.g., "alpha_vantage", "yfinance")
        bid: Bid price (optional, for real-time quotes)
        ask: Ask price (optional, for real-time quotes)
        high_24h: 24-hour high (optional)
        low_24h: 24-hour low (optional)
        open: Opening price for the period (optional)
        close: Closing price for the period (optional)
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "asset_type": "stock",
                "price": 175.50,
                "timestamp": "2025-11-07T10:30:00Z",
                "currency": "USD",
                "volume": 50000000,
                "source": "alpha_vantage"
            }
        }
    )
    
    symbol: str = Field(..., description="Asset identifier")
    asset_type: AssetType = Field(..., description="Type of asset")
    price: float = Field(..., gt=0, description="Current price (must be positive)")
    timestamp: datetime = Field(..., description="Price observation timestamp")
    currency: str = Field(default="USD", description="Base currency")
    volume: Optional[float] = Field(default=None, ge=0, description="Trading volume")
    source: str = Field(..., description="Data source")
    
    # Optional fields for more detailed quotes
    bid: Optional[float] = Field(default=None, gt=0)
    ask: Optional[float] = Field(default=None, gt=0)
    high_24h: Optional[float] = Field(default=None, gt=0)
    low_24h: Optional[float] = Field(default=None, gt=0)
    open: Optional[float] = Field(default=None, gt=0)
    close: Optional[float] = Field(default=None, gt=0)
    
    @field_validator('symbol')
    @classmethod
    def symbol_must_be_uppercase(cls, v: str) -> str:
        """Normalize symbols to uppercase."""
        return v.upper().strip()
    
    @field_validator('currency')
    @classmethod
    def currency_must_be_uppercase(cls, v: str) -> str:
        """Normalize currency codes to uppercase."""
        return v.upper().strip()


class HistoricalPrice(BaseModel):
    """
    Collection of historical prices for an asset.
    
    Attributes:
        symbol: Asset identifier
        asset_type: Type of asset
        prices: List of price observations
        start_date: Start of the time range
        end_date: End of the time range
        interval: Time interval between prices (e.g., "1d", "1h", "5m")
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "AAPL",
                "asset_type": "stock",
                "prices": [
                    {
                        "symbol": "AAPL",
                        "asset_type": "stock",
                        "price": 175.50,
                        "timestamp": "2025-11-07T10:30:00Z",
                        "currency": "USD",
                        "volume": 50000000,
                        "source": "alpha_vantage"
                    }
                ],
                "start_date": "2025-11-01T00:00:00Z",
                "end_date": "2025-11-07T23:59:59Z",
                "interval": "1d"
            }
        }
    )
    
    symbol: str
    asset_type: AssetType
    prices: List[Price] = Field(..., min_length=1)
    start_date: datetime
    end_date: datetime
    interval: str = Field(default="1d", description="Price interval")
    
    @field_validator('prices')
    @classmethod
    def prices_must_be_sorted(cls, v: List[Price]) -> List[Price]:
        """Ensure prices are sorted by timestamp."""
        return sorted(v, key=lambda p: p.timestamp)
    
    @field_validator('symbol')
    @classmethod
    def symbol_must_be_uppercase(cls, v: str) -> str:
        """Normalize symbols to uppercase."""
        return v.upper().strip()


class FetcherError(Exception):
    """Base exception for fetcher-related errors."""
    pass


class SymbolNotFoundError(FetcherError):
    """Raised when a symbol is not found."""
    def __init__(self, symbol: str, source: str):
        self.symbol = symbol
        self.source = source
        super().__init__(f"Symbol '{symbol}' not found in {source}")


class RateLimitError(FetcherError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, source: str, retry_after: Optional[int] = None):
        self.source = source
        self.retry_after = retry_after
        msg = f"Rate limit exceeded for {source}"
        if retry_after:
            msg += f". Retry after {retry_after} seconds"
        super().__init__(msg)


class APIError(FetcherError):
    """Raised when API returns an error."""
    def __init__(self, source: str, status_code: int, message: str):
        self.source = source
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error from {source} ({status_code}): {message}")