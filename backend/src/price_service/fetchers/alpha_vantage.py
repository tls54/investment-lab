"""
Alpha Vantage API client for fetching stock and commodity prices.

Alpha Vantage provides free API access with rate limits:
- Free tier: 500 calls/day, 5 calls/minute
- Supports stocks, forex, commodities, and crypto

API Documentation: https://www.alphavantage.co/documentation/
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import httpx

from .base import BaseFetcherWithCache
from ..models import (
    Price, HistoricalPrice, AssetType,
    SymbolNotFoundError, APIError, RateLimitError
)


logger = logging.getLogger(__name__)


class AlphaVantageFetcher(BaseFetcherWithCache):
    """
    Fetcher for Alpha Vantage API.
    
    Supports:
    - Stocks (US and international)
    - Commodities (via WTI, Brent, Natural Gas, etc.)
    - Forex
    - Crypto (limited)
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(
        self,
        api_key: str,
        rate_limit_per_minute: int = 5,
        cache_ttl_seconds: int = 60,
        timeout: int = 30
    ):
        """
        Initialize Alpha Vantage fetcher.
        
        Args:
            api_key: Alpha Vantage API key
            rate_limit_per_minute: API calls per minute (default: 5 for free tier)
            cache_ttl_seconds: Cache TTL in seconds
            timeout: HTTP request timeout in seconds
        """
        super().__init__(api_key, rate_limit_per_minute, cache_ttl_seconds)
        self.timeout = timeout
        
        if not api_key:
            raise ValueError("Alpha Vantage API key is required")
    
    @property
    def name(self) -> str:
        return "Alpha Vantage"
    
    @property
    def supported_asset_types(self) -> List[AssetType]:
        return [
            AssetType.STOCK,
            AssetType.ETF,
            AssetType.COMMODITY,
            AssetType.FOREX,
            AssetType.CRYPTO
        ]
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Make HTTP request to Alpha Vantage API.
        
        Args:
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            RateLimitError: If rate limit exceeded
            APIError: If API returns an error
        """
        await self._check_rate_limit()
        
        params["apikey"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Check for API-specific errors
                if "Error Message" in data:
                    raise SymbolNotFoundError(
                        params.get("symbol", "unknown"),
                        self.name
                    )
                
                if "Note" in data:
                    # Rate limit message from API
                    logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                    raise RateLimitError(self.name, retry_after=60)
                
                if "Information" in data:
                    # Usually rate limit info
                    logger.warning(f"Alpha Vantage info: {data['Information']}")
                    raise RateLimitError(self.name, retry_after=60)
                
                return data
                
        except httpx.HTTPStatusError as e:
            raise APIError(self.name, e.response.status_code, str(e))
        except httpx.RequestError as e:
            raise APIError(self.name, 0, f"Request failed: {str(e)}")
    
    async def fetch_price(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None
    ) -> Price:
        """
        Fetch current price for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "MSFT")
            asset_type: Asset type (defaults to STOCK)
            
        Returns:
            Price object with current data
        """
        symbol = symbol.upper().strip()
        asset_type = asset_type or AssetType.STOCK
        
        # Check cache
        cache_key = self._get_cache_key("price", symbol, asset_type)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Determine function based on asset type
        if asset_type == AssetType.STOCK or asset_type == AssetType.ETF:
            function = "GLOBAL_QUOTE"
        elif asset_type == AssetType.CRYPTO:
            function = "CURRENCY_EXCHANGE_RATE"
        else:
            # For commodities and forex, we'll use TIME_SERIES_INTRADAY
            function = "TIME_SERIES_INTRADAY"
        
        params = {
            "function": function,
            "symbol": symbol
        }
        
        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = "1min"
        
        data = await self._make_request(params)
        
        # Parse response based on function type
        if function == "GLOBAL_QUOTE":
            quote = data.get("Global Quote", {})
            if not quote:
                raise SymbolNotFoundError(symbol, self.name)
            
            price_obj = Price(
                symbol=symbol,
                asset_type=asset_type,
                price=float(quote["05. price"]),
                timestamp=datetime.now(),  # AV doesn't provide exact timestamp
                volume=float(quote.get("06. volume", 0)),
                open=float(quote.get("02. open", 0)),
                high_24h=float(quote.get("03. high", 0)),
                low_24h=float(quote.get("04. low", 0)),
                close=float(quote.get("08. previous close", 0)),
                currency="USD",
                source=self.name
            )
        
        elif function == "CURRENCY_EXCHANGE_RATE":
            rate_data = data.get("Realtime Currency Exchange Rate", {})
            if not rate_data:
                raise SymbolNotFoundError(symbol, self.name)
            
            price_obj = Price(
                symbol=symbol,
                asset_type=asset_type,
                price=float(rate_data["5. Exchange Rate"]),
                timestamp=datetime.strptime(
                    rate_data["6. Last Refreshed"],
                    "%Y-%m-%d %H:%M:%S"
                ),
                currency=rate_data["3. To_Currency Code"],
                source=self.name
            )
        
        else:  # TIME_SERIES_INTRADAY
            time_series_key = f"Time Series (1min)"
            time_series = data.get(time_series_key, {})
            
            if not time_series:
                raise SymbolNotFoundError(symbol, self.name)
            
            # Get most recent data point
            latest_timestamp = max(time_series.keys())
            latest_data = time_series[latest_timestamp]
            
            price_obj = Price(
                symbol=symbol,
                asset_type=asset_type,
                price=float(latest_data["4. close"]),
                timestamp=datetime.strptime(latest_timestamp, "%Y-%m-%d %H:%M:%S"),
                volume=float(latest_data.get("5. volume", 0)),
                open=float(latest_data["1. open"]),
                high_24h=float(latest_data["2. high"]),
                low_24h=float(latest_data["3. low"]),
                close=float(latest_data["4. close"]),
                currency="USD",
                source=self.name
            )
        
        # Cache the result
        self._set_in_cache(cache_key, price_obj)
        
        logger.info(f"Fetched price for {symbol}: ${price_obj.price}")
        return price_obj
    
    async def fetch_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        asset_type: Optional[AssetType] = None
    ) -> HistoricalPrice:
        """
        Fetch historical prices for a symbol.
        
        Args:
            symbol: Stock symbol
            start: Start date
            end: End date
            interval: Time interval ("1d" for daily, "1h" for hourly, etc.)
            asset_type: Asset type (defaults to STOCK)
            
        Returns:
            HistoricalPrice object with time series
        """
        symbol = symbol.upper().strip()
        asset_type = asset_type or AssetType.STOCK
        
        # Check cache
        cache_key = self._get_cache_key(
            "historical", symbol, start.date(), end.date(), interval
        )
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        # Determine function based on interval
        if interval == "1d":
            function = "TIME_SERIES_DAILY"
            outputsize = "full"  # Get all available data
        elif interval in ["1h", "60m"]:
            function = "TIME_SERIES_INTRADAY"
            outputsize = "full"
        else:
            function = "TIME_SERIES_INTRADAY"
            outputsize = "full"
        
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        if function == "TIME_SERIES_INTRADAY":
            # Map interval to AV format
            interval_map = {
                "1m": "1min",
                "5m": "5min",
                "15m": "15min",
                "30m": "30min",
                "1h": "60min",
                "60m": "60min"
            }
            params["interval"] = interval_map.get(interval, "60min")
        
        data = await self._make_request(params)
        
        # Determine time series key
        if function == "TIME_SERIES_DAILY":
            time_series_key = "Time Series (Daily)"
        else:
            time_series_key = f"Time Series ({params['interval']})"
        
        time_series = data.get(time_series_key, {})
        
        if not time_series:
            raise SymbolNotFoundError(symbol, self.name)
        
        # Parse all data points
        prices = []
        for timestamp_str, values in time_series.items():
            timestamp = datetime.strptime(
                timestamp_str,
                "%Y-%m-%d %H:%M:%S" if " " in timestamp_str else "%Y-%m-%d"
            )
            
            # Filter by date range
            if timestamp < start or timestamp > end:
                continue
            
            price_obj = Price(
                symbol=symbol,
                asset_type=asset_type,
                price=float(values["4. close"]),
                timestamp=timestamp,
                volume=float(values.get("5. volume", 0)),
                open=float(values["1. open"]),
                high_24h=float(values["2. high"]),
                low_24h=float(values["3. low"]),
                close=float(values["4. close"]),
                currency="USD",
                source=self.name
            )
            prices.append(price_obj)
        
        if not prices:
            logger.warning(
                f"No historical data found for {symbol} "
                f"between {start.date()} and {end.date()}"
            )
        
        historical = HistoricalPrice(
            symbol=symbol,
            asset_type=asset_type,
            prices=prices,
            start_date=start,
            end_date=end,
            interval=interval
        )
        
        # Cache the result
        self._set_in_cache(cache_key, historical)
        
        logger.info(
            f"Fetched {len(prices)} historical prices for {symbol} "
            f"from {start.date()} to {end.date()}"
        )
        
        return historical
    
    async def validate_symbol(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None
    ) -> bool:
        """
        Validate if a symbol exists.
        
        Args:
            symbol: Symbol to validate
            asset_type: Asset type
            
        Returns:
            True if symbol is valid
        """
        try:
            await self.fetch_price(symbol, asset_type)
            return True
        except SymbolNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False