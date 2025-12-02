"""
yfinance fetcher for stock, ETF, and crypto prices.

yfinance is a free, unlimited alternative to Alpha Vantage.
Supports stocks, ETFs, and cryptocurrencies via -USD suffix (e.g., BTC-USD).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import yfinance as yf
import pytz

from .base import AssetFetcher
from ..models import Price, HistoricalPrice, AssetType, SymbolNotFoundError, APIError, NoDataAvailableError


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
        currency: Optional[str] = "USD"
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
        if currency is None:
            currency = "USD"
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
        currency: Optional[str] = None
    ) -> Price:
        """
        Fetch current price for a stock/ETF/crypto.

        Tries direct pair first (e.g., BTC-INR), falls back to triangular
        conversion via USD if direct pair is not available.

        Args:
            symbol: Stock/crypto symbol (e.g., "AAPL", "BTC")
            asset_type: STOCK, ETF, or CRYPTO
            currency: Fiat currency for crypto prices (e.g., "USD", "EUR", "GBP").
                     If None, returns asset in its native currency (USD for US stocks, GBP for .L stocks, etc.)

        Returns:
            Price object with current data
        """
        # Default to USD for crypto if not specified, None for stocks (use native currency)
        if currency is None:
            currency = "USD"

        try:
            # Try direct pair first (most accurate)
            return await self._fetch_price_direct(symbol, asset_type, currency, currency_explicitly_requested=(currency != "USD"))

        except SymbolNotFoundError:
            # If direct pair fails, try triangular conversion
            if self._should_try_triangular(asset_type, currency):
                logger.info(
                    f"Direct pair {symbol}-{currency} not found, "
                    f"attempting triangular conversion via USD"
                )
                return await self._fetch_price_triangular(symbol, asset_type, currency)
            else:
                # Re-raise if triangular not applicable
                raise

    def _should_try_triangular(
        self,
        asset_type: Optional[AssetType],
        currency: Optional[str]
    ) -> bool:
        """
        Determine if triangular conversion should be attempted AT THE FETCHER LEVEL.

        Fetcher-level triangular conversion is only applicable when:
        1. Asset is crypto (stocks/ETFs are fetched in native exchange currency only)
        2. Currency is not USD (prevents infinite loop)

        Note: This is a fetcher-level restriction. The DenominationConverter layer
        provides cross-currency support for ALL asset types (stocks, ETFs, crypto)
        via forex rate conversion. Use converter.convert_to_currency() for stock
        currency conversions and converter.convert() for cross-currency asset comparisons.

        Args:
            asset_type: Type of asset
            currency: Target currency

        Returns:
            True if triangular conversion should be attempted at fetcher level
        """
        # Only for crypto
        if asset_type != AssetType.CRYPTO:
            return False

        # Don't try if already USD (would create loop) or if currency is None (defaults to USD)
        if currency is None or currency.upper().strip() == "USD":
            return False

        return True

    async def _fetch_price_direct(
        self,
        symbol: str,
        asset_type: Optional[AssetType] = None,
        currency: str = "USD",
        currency_explicitly_requested: bool = False
    ) -> Price:
        """
        Fetch price directly from yfinance (without triangular conversion).

        This is the original fetch_price implementation.

        Args:
            symbol: Stock/crypto symbol
            asset_type: STOCK, ETF, or CRYPTO
            currency: Fiat currency for crypto prices
            currency_explicitly_requested: True if user explicitly requested this currency

        Returns:
            Price object with current data

        Raises:
            SymbolNotFoundError: If symbol/pair not found
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

            # Get the actual currency returned by yfinance
            actual_currency = info.get('currency', 'USD')

            # Validate currency for non-crypto assets ONLY if user explicitly requested a specific currency
            # Stocks/ETFs should only be fetched in their native exchange currency
            if (asset_type in (AssetType.STOCK, AssetType.ETF) and
                currency_explicitly_requested and
                currency.upper() != actual_currency.upper()):
                raise SymbolNotFoundError(
                    f"{original_symbol} in {currency.upper()} (not available at fetcher level - "
                    f"{original_symbol} is traded in {actual_currency}. "
                    f"Use converter.convert_to_currency() for currency conversion)",
                    self.name
                )

            price_obj = Price(
                symbol=original_symbol,  # Use original symbol without -USD suffix
                asset_type=asset_type,
                price=float(current_price),
                timestamp=datetime.now(),
                currency=actual_currency,
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

    async def _fetch_forex_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Fetch forex exchange rate from yfinance.

        yfinance uses format: {FROM}{TO}=X for forex pairs
        Example: USDINR=X for USD to INR rate

        Args:
            from_currency: Source currency (e.g., "USD")
            to_currency: Target currency (e.g., "INR")

        Returns:
            Exchange rate (e.g., 83.12 means 1 USD = 83.12 INR)

        Raises:
            APIError: If forex rate cannot be fetched
        """
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # yfinance forex format: {FROM}{TO}=X
        forex_symbol = f"{from_currency}{to_currency}=X"

        try:
            ticker = yf.Ticker(forex_symbol)
            info = ticker.info

            # Get current rate
            rate = info.get('regularMarketPrice')

            if rate is None or rate <= 0:
                raise ValueError(f"Invalid forex rate: {rate}")

            logger.info(f"Forex rate {from_currency}/{to_currency}: {rate}")
            return float(rate)

        except Exception as e:
            logger.error(f"Failed to fetch forex rate {forex_symbol}: {e}")
            raise APIError(
                self.name,
                0,
                f"Unable to fetch forex rate {from_currency}/{to_currency}: {e}"
            )

    async def _fetch_forex_historical(
        self,
        from_currency: str,
        to_currency: str,
        start: datetime,
        end: datetime,
        interval: str = "1d"
    ) -> Dict[datetime.date, float]:
        """
        Fetch historical forex exchange rates from yfinance.

        yfinance uses format: {FROM}{TO}=X for forex pairs
        Example: USDINR=X for USD to INR historical rates

        Args:
            from_currency: Source currency (e.g., "USD")
            to_currency: Target currency (e.g., "INR")
            start: Start date for historical data
            end: End date for historical data
            interval: Time interval (default "1d")

        Returns:
            Dictionary mapping date -> forex rate
            Example: {date(2024,1,1): 83.12, date(2024,1,2): 83.15, ...}

        Raises:
            APIError: If forex rates cannot be fetched
        """
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # yfinance forex format: {FROM}{TO}=X
        forex_symbol = f"{from_currency}{to_currency}=X"

        try:
            ticker = yf.Ticker(forex_symbol)

            # Fetch historical data
            hist = ticker.history(start=start, end=end, interval=interval)

            if hist.empty:
                raise ValueError(f"No historical data available for {forex_symbol}")

            # Build dictionary mapping date -> rate
            forex_rates = {}
            for timestamp, row in hist.iterrows():
                date = timestamp.date()
                rate = float(row['Close'])

                if rate <= 0:
                    logger.warning(f"Invalid forex rate {rate} for {forex_symbol} on {date}")
                    continue

                forex_rates[date] = rate

            if not forex_rates:
                raise ValueError(f"No valid forex rates found for {forex_symbol}")

            logger.info(
                f"Fetched {len(forex_rates)} historical forex rates for "
                f"{from_currency}/{to_currency} from {start.date()} to {end.date()}"
            )

            return forex_rates

        except Exception as e:
            logger.error(f"Failed to fetch historical forex rates {forex_symbol}: {e}")
            raise APIError(
                self.name,
                0,
                f"Unable to fetch historical forex rates {from_currency}/{to_currency}: {e}"
            )

    async def _fetch_price_triangular(
        self,
        symbol: str,
        asset_type: AssetType,
        currency: str
    ) -> Price:
        """
        Fetch price using triangular conversion via USD.

        Example: BTC-INR = BTC-USD × USD-INR

        This is used as a fallback when direct pair (e.g., BTC-INR) is not
        available from yfinance.

        Args:
            symbol: Crypto symbol (e.g., "BTC")
            asset_type: Should be CRYPTO
            currency: Target currency (e.g., "INR")

        Returns:
            Price object with calculated price in target currency

        Raises:
            SymbolNotFoundError: If triangular conversion fails
        """
        logger.info(
            f"Triangular conversion: {symbol}-{currency} "
            f"via {symbol}-USD × USD-{currency}"
        )

        try:
            # Step 1: Fetch crypto price in USD
            crypto_usd = await self._fetch_price_direct(symbol, asset_type, "USD")

            # Step 2: Fetch forex rate USD → target currency
            forex_rate = await self._fetch_forex_rate("USD", currency)

            # Step 3: Calculate price in target currency
            calculated_price = crypto_usd.price * forex_rate

            logger.info(
                f"Triangular conversion successful: "
                f"{symbol} ${crypto_usd.price:.2f} × {forex_rate:.4f} "
                f"= {calculated_price:.2f} {currency}"
            )

            # Step 4: Build Price object with calculated values
            # Convert all USD values to target currency
            return Price(
                symbol=symbol,
                asset_type=asset_type,
                price=calculated_price,
                timestamp=datetime.now(),
                currency=currency,
                volume=crypto_usd.volume,  # Volume stays the same
                open=crypto_usd.open * forex_rate if crypto_usd.open else None,
                high_24h=crypto_usd.high_24h * forex_rate if crypto_usd.high_24h else None,
                low_24h=crypto_usd.low_24h * forex_rate if crypto_usd.low_24h else None,
                close=crypto_usd.close * forex_rate if crypto_usd.close else None,
                source=f"{self.name} (triangular)",  # Mark as triangular
                bid=crypto_usd.bid * forex_rate if crypto_usd.bid else None,
                ask=crypto_usd.ask * forex_rate if crypto_usd.ask else None
            )

        except Exception as e:
            logger.error(
                f"Triangular conversion failed for {symbol}-{currency}: {e}"
            )
            raise SymbolNotFoundError(
                f"{symbol} with currency {currency}",
                self.name
            )
    
    async def fetch_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        asset_type: Optional[AssetType] = None,
        currency: Optional[str] = None
    ) -> HistoricalPrice:
        """
        Fetch historical prices for a stock/ETF/crypto.

        Args:
            symbol: Stock/crypto symbol
            start: Start date
            end: End date
            interval: Time interval ("1d", "1h", "5m", etc.)
            asset_type: STOCK, ETF, or CRYPTO
            currency: Fiat currency for crypto prices (e.g., "USD", "EUR", "GBP").
                     If None, returns asset in its native currency.

        Returns:
            HistoricalPrice object with time series
        """
        original_symbol = symbol.upper().strip()

        # Default to USD for crypto if not specified
        if currency is None:
            currency = "USD"

        # Normalize crypto symbols (add currency suffix if needed)
        normalized_symbol = self._normalize_crypto_symbol(original_symbol, asset_type, currency)

        try:
            ticker = yf.Ticker(normalized_symbol)

            # Map our interval to yfinance format
            yf_interval = interval
            if interval == "1h":
                yf_interval = "1h"
            elif interval == "30m":
                yf_interval = "30m"
            elif interval == "90m":
                yf_interval = "90m"
            elif interval == "5m":
                yf_interval = "5m"
            elif interval == "1d":
                yf_interval = "1d"

            # For intraday intervals (1h, 5m), yfinance works better with 'period' parameter
            # for short time ranges (< 60 days). For longer ranges, use start/end.
            days_diff = (end - start).days

            if yf_interval in ["1h", "5m", "15m", "30m", "90m"] and days_diff <= 59:
                # Use period parameter for intraday data
                # yfinance periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
                if days_diff == 0:
                    # Today - use 1d period
                    period = "1d"
                elif days_diff <= 1:
                    # Last 24 hours - use 5d to ensure we get enough data
                    period = "5d"
                elif days_diff <= 7:
                    period = "5d"
                elif days_diff <= 30:
                    period = "1mo"
                else:
                    period = "3mo"

                logger.info(f"Using period={period} interval={yf_interval} for {original_symbol}")
                hist = ticker.history(period=period, interval=yf_interval)

                # Filter the results to match the requested date range
                if not hist.empty:
                    # Convert start/end to timezone-aware if hist.index is timezone-aware
                    if hist.index.tz is not None:
                        # Make start/end timezone-aware (convert to UTC)
                        if start.tzinfo is None:
                            start = pytz.utc.localize(start)
                        if end.tzinfo is None:
                            end = pytz.utc.localize(end)

                    # Add a small buffer to end time to ensure we capture the last data point
                    # This handles timezone rounding and market close timing issues
                    end_with_buffer = end + timedelta(hours=1)
                    hist = hist[(hist.index >= start) & (hist.index <= end_with_buffer)]
            else:
                # Use start/end for daily data or longer ranges
                logger.info(f"Using start={start.date()} end={end.date()} interval={yf_interval} for {original_symbol}")
                hist = ticker.history(start=start, end=end, interval=yf_interval)

            # Check if we got any data
            if hist.empty:
                # Check if symbol is valid by looking at ticker info
                info = ticker.info

                # If info is empty or doesn't have basic fields, symbol doesn't exist
                if not info or 'regularMarketPrice' not in info:
                    raise SymbolNotFoundError(original_symbol, self.name)

                # Symbol exists but no data for this period (e.g., non-trading day)
                raise NoDataAvailableError(
                    original_symbol,
                    self.name,
                    start_date=start.strftime("%Y-%m-%d"),
                    end_date=end.strftime("%Y-%m-%d")
                )

            # Determine asset type and get actual currency from yfinance
            info = ticker.info
            if asset_type is None:
                quote_type = info.get('quoteType', 'EQUITY')
                if quote_type == 'CRYPTOCURRENCY':
                    asset_type = AssetType.CRYPTO
                elif quote_type == 'ETF':
                    asset_type = AssetType.ETF
                else:
                    asset_type = AssetType.STOCK

            # Get actual currency from yfinance (not the parameter!)
            actual_currency = info.get('currency', currency)

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
                    currency=actual_currency,  # Use actual currency from yfinance
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

        except (SymbolNotFoundError, NoDataAvailableError):
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