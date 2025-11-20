"""
yfinance fetcher for stock, ETF, and crypto prices.

yfinance is a free, unlimited alternative to Alpha Vantage.
Supports stocks, ETFs, and cryptocurrencies via -USD suffix (e.g., BTC-USD).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
import yfinance as yf

from .base import AssetFetcher
from ..models import Price, HistoricalPrice, AssetType, SymbolNotFoundError, APIError


logger = logging.getLogger(__name__)


class YFinanceFetcher(AssetFetcher):
    """
    Fetcher using yfinance library.

    Advantages:
    - Free, no API key required
    - No rate limits
    - Good for US stocks and major international stocks
    - Supports cryptocurrencies via -USD suffix

    Limitations:
    - Data may be slightly delayed
    - Less reliable than paid APIs
    """

    # Common cryptocurrency symbols that need -USD suffix
    CRYPTO_SYMBOLS = {
        "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP", "DOGE", "ADA", "TRX",
        "AVAX", "LINK", "DOT", "MATIC", "UNI", "LTC", "BCH", "XLM", "ATOM", "ETC"
    }

    def __init__(self):
        """Initialize yfinance fetcher (no API key needed)."""
        super().__init__(api_key=None, rate_limit_per_minute=None)

    @property
    def name(self) -> str:
        return "yfinance"

    @property
    def supported_asset_types(self) -> List[AssetType]:
        return [AssetType.STOCK, AssetType.ETF, AssetType.CRYPTO]

    def _normalize_crypto_symbol(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None,
        currency: str = "USD"
    ) -> str:
        """
        Normalize crypto symbols for yfinance.

        yfinance requires crypto symbols to have currency suffix (e.g., BTC-USD, BTC-EUR).
        This method automatically adds the suffix if needed.

        Args:
            symbol: Raw symbol (e.g., "BTC" or "BTC-USD")
            asset_type: Asset type (helps determine if it's crypto)
            currency: Fiat currency to price the crypto in (default: "USD")

        Returns:
            Normalized symbol for yfinance (e.g., "BTC-USD", "BTC-EUR")
        """
        symbol = symbol.upper().strip()
        currency = currency.upper().strip()

        # If already has a currency suffix, return as-is
        if "-" in symbol and len(symbol.split("-")) == 2:
            return symbol

        # Check if it's a known crypto symbol or if asset_type is CRYPTO
        if asset_type == AssetType.CRYPTO or symbol in self.CRYPTO_SYMBOLS:
            return f"{symbol}-{currency}"

        return symbol
    
    async def fetch_price(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None,
        currency: str = "USD"
    ) -> Price:
        """
        Fetch current price for a stock/ETF/crypto.

        Args:
            symbol: Stock/crypto symbol (e.g., "AAPL", "BTC")
            asset_type: STOCK, ETF, or CRYPTO
            currency: Fiat currency for crypto prices (e.g., "USD", "EUR", "GBP")

        Returns:
            Price object with current data
        """
        original_symbol = symbol.upper().strip()

        # Normalize crypto symbols (add currency suffix if needed)
        normalized_symbol = self._normalize_crypto_symbol(original_symbol, asset_type, currency)

        try:
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info

            # Check if symbol is valid
            if not info or 'regularMarketPrice' not in info:
                raise SymbolNotFoundError(original_symbol, self.name)

            # Get current price
            current_price = info.get('regularMarketPrice')
            if current_price is None or current_price == 0:
                raise SymbolNotFoundError(original_symbol, self.name)

            # Determine asset type
            if asset_type is None:
                quote_type = info.get('quoteType', 'EQUITY')
                if quote_type == 'CRYPTOCURRENCY':
                    asset_type = AssetType.CRYPTO
                elif quote_type == 'ETF':
                    asset_type = AssetType.ETF
                else:
                    asset_type = AssetType.STOCK

            price_obj = Price(
                symbol=original_symbol,  # Use original symbol without -USD suffix
                asset_type=asset_type,
                price=float(current_price),
                timestamp=datetime.now(),
                currency=info.get('currency', 'USD'),
                volume=float(info.get('regularMarketVolume', 0)),
                open=float(info.get('regularMarketOpen', 0)) if info.get('regularMarketOpen') else None,
                high_24h=float(info.get('dayHigh', 0)) if info.get('dayHigh') else None,
                low_24h=float(info.get('dayLow', 0)) if info.get('dayLow') else None,
                close=float(info.get('previousClose', 0)) if info.get('previousClose') else None,
                bid=float(info.get('bid', 0)) if info.get('bid') else None,
                ask=float(info.get('ask', 0)) if info.get('ask') else None,
                source=self.name
            )

            logger.info(f"Fetched price for {original_symbol}: ${price_obj.price}")
            return price_obj

        except SymbolNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching price for {original_symbol}: {e}")
            raise APIError(self.name, 0, str(e))
    
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
        Fetch historical prices for a stock/ETF/crypto.

        Args:
            symbol: Stock/crypto symbol
            start: Start date
            end: End date
            interval: Time interval ("1d", "1h", "5m", etc.)
            asset_type: STOCK, ETF, or CRYPTO
            currency: Fiat currency for crypto prices (e.g., "USD", "EUR", "GBP")

        Returns:
            HistoricalPrice object with time series
        """
        original_symbol = symbol.upper().strip()

        # Normalize crypto symbols (add currency suffix if needed)
        normalized_symbol = self._normalize_crypto_symbol(original_symbol, asset_type, currency)

        try:
            ticker = yf.Ticker(normalized_symbol)

            # Map our interval to yfinance format
            yf_interval = interval
            if interval == "1h":
                yf_interval = "1h"
            elif interval == "5m":
                yf_interval = "5m"
            elif interval == "1d":
                yf_interval = "1d"

            # Fetch historical data
            hist = ticker.history(start=start, end=end, interval=yf_interval)

            if hist.empty:
                raise SymbolNotFoundError(original_symbol, self.name)

            # Determine asset type
            if asset_type is None:
                info = ticker.info
                quote_type = info.get('quoteType', 'EQUITY')
                if quote_type == 'CRYPTOCURRENCY':
                    asset_type = AssetType.CRYPTO
                elif quote_type == 'ETF':
                    asset_type = AssetType.ETF
                else:
                    asset_type = AssetType.STOCK

            # Convert to Price objects
            prices = []
            for timestamp, row in hist.iterrows():
                price_obj = Price(
                    symbol=original_symbol,  # Use original symbol without currency suffix
                    asset_type=asset_type,
                    price=float(row['Close']),
                    timestamp=timestamp.to_pydatetime(),
                    volume=float(row['Volume']) if 'Volume' in row else 0,
                    open=float(row['Open']) if 'Open' in row else None,
                    high_24h=float(row['High']) if 'High' in row else None,
                    low_24h=float(row['Low']) if 'Low' in row else None,
                    close=float(row['Close']),
                    currency=currency,
                    source=self.name
                )
                prices.append(price_obj)

            historical = HistoricalPrice(
                symbol=original_symbol,  # Use original symbol without -USD suffix
                asset_type=asset_type,
                prices=prices,
                start_date=start,
                end_date=end,
                interval=interval
            )

            logger.info(
                f"Fetched {len(prices)} historical prices for {original_symbol} "
                f"from {start.date()} to {end.date()}"
            )

            return historical

        except SymbolNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching historical data for {original_symbol}: {e}")
            raise APIError(self.name, 0, str(e))
    
    async def validate_symbol(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None
    ) -> bool:
        """
        Validate if a stock/ETF symbol exists.
        
        Args:
            symbol: Symbol to validate
            asset_type: Asset type (ignored for yfinance)
            
        Returns:
            True if symbol is valid
        """
        try:
            await self.fetch_price(symbol, asset_type)
            return True
        except SymbolNotFoundError:
            return False
        except Exception:
            return False