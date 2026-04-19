"""
Denomination converter for pricing assets in terms of other assets.

This module allows pricing any asset in terms of any other asset.
Example: AAPL priced in BTC, SPY priced in Gold, etc.

Also supports simple currency conversion (AAPL in GBP).
"""

from typing import Optional, List, Tuple
from datetime import datetime
import bisect
import logging

from .models import Price, HistoricalPrice, AssetType
from .fetchers import AlphaVantageFetcher, YFinanceFetcher


logger = logging.getLogger(__name__)


# Common currency codes (ISO 4217)
CURRENCY_CODES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "CNY", "INR", "SGD", "HKD", "KRW", "MXN", "BRL", "ZAR"
}


def is_currency_code(symbol: str) -> bool:
    """
    Check if a symbol is a currency code rather than an asset symbol.

    Args:
        symbol: Symbol to check (e.g., "USD", "GBP", "BTC-USD")

    Returns:
        True if it's a currency code, False if it's an asset symbol
    """
    symbol_upper = symbol.upper().strip()
    return symbol_upper in CURRENCY_CODES


class DenominationConverter:
    """
    Convert asset prices to different denominations.
    
    This is the core feature that makes Investment Lab unique.
    Instead of always pricing in USD, price anything in anything!
    
    Examples:
        converter = DenominationConverter(fetchers)
        
        # How much Bitcoin is one Apple share?
        ratio = await converter.convert("AAPL", "BTC")
        # ratio = 0.00417 (AAPL costs 0.00417 BTC)
        
        # Get historical series
        history = await converter.convert_historical("AAPL", "BTC", days=30)
    """
    
    def __init__(self, fetchers: dict):
        """
        Initialize converter with available fetchers.
        
        Args:
            fetchers: Dict of {name: fetcher_instance}
        """
        self.fetchers = fetchers
    
    def _get_fetcher(self, asset_type: Optional[AssetType] = None):
        """
        Select appropriate fetcher based on asset type.

        Args:
            asset_type: Type of asset

        Returns:
            Appropriate fetcher instance
        """
        # yfinance now supports all asset types (stocks, ETFs, crypto)
        return self.fetchers["yfinance"]

    async def _fetch_forex_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Fetch forex exchange rate between two currencies.

        Args:
            from_currency: Source currency (e.g., "GBP")
            to_currency: Target currency (e.g., "USD")

        Returns:
            Exchange rate (e.g., 1.27 means 1 GBP = 1.27 USD)
        """
        fetcher = self.fetchers["yfinance"]
        return await fetcher._fetch_forex_rate(from_currency, to_currency)

    def _match_forex_rate_to_date(
        self,
        target_date: datetime.date,
        forex_rates: dict,
        max_days_back: int = 7
    ) -> Optional[float]:
        """
        Match a target date to the nearest forex rate.

        Handles weekends and holidays by looking backwards up to max_days_back days
        to find the most recent forex rate available.

        Args:
            target_date: The date to find a forex rate for
            forex_rates: Dictionary mapping date -> forex rate
            max_days_back: Maximum days to look backwards (default 7)

        Returns:
            Forex rate for the target date or nearest previous date, or None if not found
        """
        from datetime import timedelta

        # Try exact match first
        if target_date in forex_rates:
            return forex_rates[target_date]

        # Look backwards for the nearest previous rate
        for days_back in range(1, max_days_back + 1):
            previous_date = target_date - timedelta(days=days_back)
            if previous_date in forex_rates:
                logger.debug(
                    f"Using forex rate from {previous_date} for {target_date} "
                    f"({days_back} days back)"
                )
                return forex_rates[previous_date]

        # No rate found within max_days_back
        logger.warning(
            f"No forex rate found for {target_date} within {max_days_back} days"
        )
        return None

    async def convert_to_currency(
        self,
        asset_symbol: str,
        target_currency: str,
        asset_type: Optional[AssetType] = None
    ) -> dict:
        """
        Convert asset price to a different currency (simple currency conversion).

        This is different from convert() - it doesn't calculate a ratio,
        just converts the asset's price to a different currency.

        Args:
            asset_symbol: Symbol of asset (e.g., "AAPL", "VUSA.L")
            target_currency: Target currency code (e.g., "USD", "GBP", "EUR")
            asset_type: Optional type of asset

        Returns:
            Dict with converted price:
            {
                "symbol": "AAPL",
                "price": 242.50,
                "currency": "USD",
                "native_price": 242.50,
                "native_currency": "USD",
                "target_currency": "GBP",
                "converted_price": 190.94,
                "forex_rate": 0.787,
                "timestamp": "2025-11-29T...",
                "conversion_method": "direct" | "forex"
            }

        Example:
            # Convert VUSA.L (priced in GBP) to USD
            result = await converter.convert_to_currency("VUSA.L", "USD")
            # result["native_price"] = 98.0, native_currency = "GBP"
            # result["converted_price"] = 124.46, target_currency = "USD"
        """
        fetcher = self._get_fetcher(asset_type)

        logger.info(f"Converting {asset_symbol} to {target_currency}")

        # Fetch the asset price in its native currency
        asset_price = await fetcher.fetch_price(asset_symbol, asset_type)

        # Check if already in target currency
        if asset_price.currency == target_currency:
            logger.info(f"{asset_symbol} already in {target_currency}, no conversion needed")
            return {
                "symbol": asset_symbol,
                "asset_type": asset_price.asset_type.value,
                "price": asset_price.price,
                "currency": asset_price.currency,
                "native_price": asset_price.price,
                "native_currency": asset_price.currency,
                "target_currency": target_currency,
                "converted_price": asset_price.price,
                "forex_rate": 1.0,
                "timestamp": asset_price.timestamp.isoformat(),
                "conversion_method": "direct",
                "interpretation": f"{asset_symbol} is already priced in {target_currency}"
            }

        # Fetch forex rate and convert
        forex_rate = await self._fetch_forex_rate(asset_price.currency, target_currency)
        converted_price = asset_price.price * forex_rate

        logger.info(
            f"Converted {asset_symbol}: {asset_price.price} {asset_price.currency} "
            f"× {forex_rate} = {converted_price} {target_currency}"
        )

        return {
            "symbol": asset_symbol,
            "asset_type": asset_price.asset_type.value,
            "price": asset_price.price,
            "currency": asset_price.currency,
            "native_price": asset_price.price,
            "native_currency": asset_price.currency,
            "target_currency": target_currency,
            "converted_price": converted_price,
            "forex_rate": forex_rate,
            "timestamp": asset_price.timestamp.isoformat(),
            "conversion_method": "forex",
            "interpretation": f"1 {asset_price.currency} = {forex_rate:.4f} {target_currency}"
        }

    async def convert(
        self,
        asset_symbol: str,
        denomination_symbol: str,
        asset_type: Optional[AssetType] = None,
        denomination_type: Optional[AssetType] = None,
        asset_currency: str = "USD",
        denomination_currency: str = "USD"
    ) -> dict:
        """
        Convert asset price to denomination.
        
        This is the main conversion function. It fetches both prices
        and calculates the ratio.
        
        Args:
            asset_symbol: Symbol of asset to price (e.g., "AAPL")
            denomination_symbol: Symbol to price it in (e.g., "BTC")
            asset_type: Optional type of asset
            denomination_type: Optional type of denomination
            
        Returns:
            Dict with conversion data:
            {
                "asset_symbol": "AAPL",
                "denomination_symbol": "BTC",
                "ratio": 0.00417,  # 1 AAPL = 0.00417 BTC
                "asset_price_usd": 175.50,
                "denomination_price_usd": 42000.00,
                "timestamp": "2025-11-08T10:30:00",
                "inverse_ratio": 239.77  # 1 BTC = 239.77 AAPL
            }
            
        Example:
            result = await converter.convert("AAPL", "BTC")
            print(f"1 AAPL = {result['ratio']:.6f} BTC")
            print(f"1 BTC = {result['inverse_ratio']:.2f} AAPL")
        """
        # Fetch both prices
        asset_fetcher = self._get_fetcher(asset_type)
        denom_fetcher = self._get_fetcher(denomination_type)

        logger.info(f"Converting {asset_symbol} to {denomination_symbol}")

        asset_price = await asset_fetcher.fetch_price(asset_symbol, asset_type, currency=asset_currency)
        denom_price = await denom_fetcher.fetch_price(denomination_symbol, denomination_type, currency=denomination_currency)

        # Check if currencies match
        conversion_method = "direct"
        asset_price_normalized = asset_price.price
        denom_price_normalized = denom_price.price
        common_currency = asset_price.currency

        if asset_price.currency != denom_price.currency:
            # Cross-currency conversion via USD triangulation
            logger.info(
                f"Currency mismatch detected: {asset_symbol} is in {asset_price.currency}, "
                f"{denomination_symbol} is in {denom_price.currency}. "
                f"Using triangular conversion via USD."
            )
            conversion_method = "triangular"
            common_currency = "USD"

            # Convert asset to USD if needed
            if asset_price.currency != "USD":
                forex_rate = await self._fetch_forex_rate(asset_price.currency, "USD")
                asset_price_normalized = asset_price.price * forex_rate
                logger.info(
                    f"Converting {asset_symbol}: {asset_price.price} {asset_price.currency} "
                    f"× {forex_rate} = {asset_price_normalized} USD"
                )
            else:
                asset_price_normalized = asset_price.price

            # Convert denomination to USD if needed
            if denom_price.currency != "USD":
                forex_rate = await self._fetch_forex_rate(denom_price.currency, "USD")
                denom_price_normalized = denom_price.price * forex_rate
                logger.info(
                    f"Converting {denomination_symbol}: {denom_price.price} {denom_price.currency} "
                    f"× {forex_rate} = {denom_price_normalized} USD"
                )
            else:
                denom_price_normalized = denom_price.price

        # Calculate ratio using normalized prices
        ratio = asset_price_normalized / denom_price_normalized
        inverse_ratio = denom_price_normalized / asset_price_normalized

        logger.info(
            f"1 {asset_symbol} = {ratio:.6f} {denomination_symbol} "
            f"({asset_price_normalized} / {denom_price_normalized}) "
            f"[method: {conversion_method}]"
        )

        return {
            "asset_symbol": asset_symbol,
            "denomination_symbol": denomination_symbol,
            "ratio": ratio,
            "asset_price": asset_price.price,
            "asset_currency": asset_price.currency,
            "denomination_price": denom_price.price,
            "denomination_currency": denom_price.currency,
            "asset_price_normalized": asset_price_normalized,
            "denomination_price_normalized": denom_price_normalized,
            "common_currency": common_currency,
            "conversion_method": conversion_method,
            "timestamp": asset_price.timestamp.isoformat(),
            "inverse_ratio": inverse_ratio,
            "interpretation": f"1 {asset_symbol} = {ratio:.6f} {denomination_symbol}",
            "inverse_interpretation": f"1 {denomination_symbol} = {inverse_ratio:.2f} {asset_symbol}"
        }

    async def convert_to_currency_historical(
        self,
        asset_symbol: str,
        target_currency: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        asset_type: Optional[AssetType] = None
    ) -> dict:
        """
        Convert historical asset prices to a different currency.

        Uses historical forex rates for accurate conversion at each time point.

        Args:
            asset_symbol: Symbol of asset
            target_currency: Target currency code
            start: Start date
            end: End date
            interval: Time interval
            asset_type: Optional asset type

        Returns:
            Dict with converted historical prices
        """
        fetcher = self._get_fetcher(asset_type)

        logger.info(
            f"Converting historical {asset_symbol} to {target_currency} "
            f"from {start.date()} to {end.date()}"
        )

        # Fetch historical data in native currency
        asset_history = await fetcher.fetch_historical(
            asset_symbol, start, end, interval, asset_type
        )

        if not asset_history.prices:
            return {
                "symbol": asset_symbol,
                "target_currency": target_currency,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "interval": interval,
                "count": 0,
                "conversion_method": "none",
                "data": []
            }

        native_currency = asset_history.prices[0].currency
        conversion_method = "direct"
        forex_rates = {}

        # Check if conversion needed
        if native_currency != target_currency:
            conversion_method = "forex_historical"
            # Fetch historical forex rates for the entire period
            forex_rates = await fetcher._fetch_forex_historical(
                native_currency, target_currency, start, end, interval
            )
            logger.info(
                f"Fetched {len(forex_rates)} historical forex rates "
                f"for {native_currency}/{target_currency}"
            )

        # Convert all price points
        data_points = []
        skipped_count = 0

        for price_obj in asset_history.prices:
            date = price_obj.timestamp.date()

            if native_currency == target_currency:
                # No conversion needed
                forex_rate = 1.0
                converted_price = price_obj.price
            else:
                # Match forex rate to this date
                forex_rate = self._match_forex_rate_to_date(date, forex_rates)

                if forex_rate is None:
                    # Skip this data point if no forex rate available
                    logger.warning(
                        f"Skipping {asset_symbol} price on {date} - no forex rate available"
                    )
                    skipped_count += 1
                    continue

                converted_price = price_obj.price * forex_rate

            data_points.append({
                "timestamp": price_obj.timestamp.isoformat(),
                "date": date.isoformat(),
                "native_price": price_obj.price,
                "native_currency": native_currency,
                "converted_price": converted_price,
                "target_currency": target_currency,
                "forex_rate": forex_rate,
                "volume": price_obj.volume,
                "open": price_obj.open * forex_rate if price_obj.open else None,
                "high": price_obj.high_24h * forex_rate if price_obj.high_24h else None,
                "low": price_obj.low_24h * forex_rate if price_obj.low_24h else None,
                "close": price_obj.close * forex_rate if price_obj.close else None
            })

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} data points due to missing forex rates")

        logger.info(f"Converted {len(data_points)} historical price points")

        return {
            "symbol": asset_symbol,
            "native_currency": native_currency,
            "target_currency": target_currency,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "interval": interval,
            "count": len(data_points),
            "conversion_method": conversion_method,
            "skipped_count": skipped_count,
            "data": data_points,
            "summary": {
                "min_price": min(d["converted_price"] for d in data_points) if data_points else None,
                "max_price": max(d["converted_price"] for d in data_points) if data_points else None,
                "avg_price": sum(d["converted_price"] for d in data_points) / len(data_points) if data_points else None
            }
        }

    async def convert_historical(
        self,
        asset_symbol: str,
        denomination_symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        asset_type: Optional[AssetType] = None,
        denomination_type: Optional[AssetType] = None,
        asset_currency: str = "USD",
        denomination_currency: str = "USD"
    ) -> dict:
        """
        Convert historical prices to denomination.
        
        This fetches historical data for both assets and calculates
        the ratio at each point in time.
        
        Args:
            asset_symbol: Asset to price
            denomination_symbol: Denomination to price in
            start: Start date
            end: End date
            interval: Time interval
            asset_type: Optional asset type
            denomination_type: Optional denomination type
            
        Returns:
            Dict with historical conversion data:
            {
                "asset_symbol": "AAPL",
                "denomination_symbol": "BTC",
                "start_date": "2025-11-01",
                "end_date": "2025-11-08",
                "interval": "1d",
                "count": 7,
                "data": [
                    {
                        "timestamp": "2025-11-01",
                        "ratio": 0.00421,
                        "asset_price_usd": 172.30,
                        "denomination_price_usd": 40900.00
                    },
                    ...
                ]
            }
            
        Example:
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=30)
            
            result = await converter.convert_historical("AAPL", "BTC", start, end)
            
            # Plot the ratio over time
            for point in result['data']:
                print(f"{point['timestamp']}: {point['ratio']:.6f} BTC")
        """
        # Fetch historical data for both assets
        asset_fetcher = self._get_fetcher(asset_type)
        denom_fetcher = self._get_fetcher(denomination_type)

        logger.info(
            f"Converting historical {asset_symbol}/{denomination_symbol} "
            f"from {start.date()} to {end.date()}"
        )

        asset_history = await asset_fetcher.fetch_historical(
            asset_symbol, start, end, interval, asset_type, currency=asset_currency
        )
        denom_history = await denom_fetcher.fetch_historical(
            denomination_symbol, start, end, interval, denomination_type, currency=denomination_currency
        )

        # Check if currencies match
        conversion_method = "direct"
        common_currency = None
        forex_rates_asset = {}  # Historical forex rates for asset currency -> USD
        forex_rates_denom = {}  # Historical forex rates for denomination currency -> USD

        if asset_history.prices and denom_history.prices:
            asset_curr = asset_history.prices[0].currency
            denom_curr = denom_history.prices[0].currency
            common_currency = asset_curr

            if asset_curr != denom_curr:
                # Cross-currency conversion via USD
                logger.info(
                    f"Currency mismatch detected in historical data: {asset_symbol} is in {asset_curr}, "
                    f"{denomination_symbol} is in {denom_curr}. Using triangular conversion via USD."
                )
                conversion_method = "triangular"
                common_currency = "USD"

                # Fetch historical forex rates for the entire period
                if asset_curr != "USD":
                    forex_rates_asset = await asset_fetcher._fetch_forex_historical(
                        asset_curr, "USD", start, end, interval
                    )
                    logger.info(
                        f"Fetched {len(forex_rates_asset)} historical forex rates for {asset_curr}/USD"
                    )

                if denom_curr != "USD":
                    forex_rates_denom = await denom_fetcher._fetch_forex_historical(
                        denom_curr, "USD", start, end, interval
                    )
                    logger.info(
                        f"Fetched {len(forex_rates_denom)} historical forex rates for {denom_curr}/USD"
                    )

        # Match up timestamps and calculate ratios
        # We'll use the asset timestamps as the reference
        data_points = []

        # Build sorted lists for nearest-timestamp denomination price lookup.
        # Using timestamp (not date) preserves intraday granularity when both
        # assets have sub-daily data (e.g. crypto/crypto or intraday stock/crypto).
        _denom_ts = [p.timestamp for p in denom_history.prices]
        _denom_px = [p.price for p in denom_history.prices]

        def _nearest_denom_price(ts: datetime) -> float:
            idx = bisect.bisect_left(_denom_ts, ts)
            if idx == 0:
                return _denom_px[0]
            if idx >= len(_denom_ts):
                return _denom_px[-1]
            before, after = _denom_ts[idx - 1], _denom_ts[idx]
            return _denom_px[idx] if (ts - before) > (after - ts) else _denom_px[idx - 1]

        skipped_count = 0

        for asset_price_obj in asset_history.prices:
            date = asset_price_obj.timestamp.date()
            denom_price = _nearest_denom_price(asset_price_obj.timestamp)

            # Normalize prices if cross-currency
            if conversion_method == "triangular":
                asset_price_normalized = asset_price_obj.price
                denom_price_normalized = denom_price
                asset_forex_rate = 1.0
                denom_forex_rate = 1.0

                # Get historical forex rate for asset currency on this date
                if asset_price_obj.currency != "USD":
                    asset_forex_rate = self._match_forex_rate_to_date(date, forex_rates_asset)
                    if asset_forex_rate is None:
                        logger.warning(
                            f"Skipping {asset_symbol} on {date} - no forex rate for {asset_price_obj.currency}/USD"
                        )
                        skipped_count += 1
                        continue
                    asset_price_normalized = asset_price_obj.price * asset_forex_rate

                # Get historical forex rate for denomination currency on this date
                if denom_history.prices[0].currency != "USD":
                    denom_forex_rate = self._match_forex_rate_to_date(date, forex_rates_denom)
                    if denom_forex_rate is None:
                        logger.warning(
                            f"Skipping {denomination_symbol} on {date} - no forex rate for {denom_history.prices[0].currency}/USD"
                        )
                        skipped_count += 1
                        continue
                    denom_price_normalized = denom_price * denom_forex_rate
            else:
                # Direct conversion (same currency)
                asset_price_normalized = asset_price_obj.price
                denom_price_normalized = denom_price
                asset_forex_rate = 1.0
                denom_forex_rate = 1.0

            ratio = asset_price_normalized / denom_price_normalized

            data_points.append({
                "timestamp": asset_price_obj.timestamp.isoformat(),
                "date": date.isoformat(),
                "ratio": ratio,
                "asset_price": asset_price_obj.price,
                "asset_currency": asset_price_obj.currency,
                "denomination_price": denom_price,
                "denomination_currency": denom_history.prices[0].currency,
                "asset_price_normalized": asset_price_normalized,
                "denomination_price_normalized": denom_price_normalized,
                "common_currency": common_currency,
                "inverse_ratio": denom_price_normalized / asset_price_normalized,
                "asset_forex_rate": asset_forex_rate,
                "denom_forex_rate": denom_forex_rate
            })

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} data points due to missing forex rates")

        logger.info(f"Generated {len(data_points)} conversion data points [method: {conversion_method}]")

        return {
            "asset_symbol": asset_symbol,
            "denomination_symbol": denomination_symbol,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "interval": interval,
            "count": len(data_points),
            "conversion_method": conversion_method,
            "common_currency": common_currency,
            "skipped_count": skipped_count,
            "data": data_points,
            "summary": {
                "min_ratio": min(d["ratio"] for d in data_points) if data_points else None,
                "max_ratio": max(d["ratio"] for d in data_points) if data_points else None,
                "avg_ratio": sum(d["ratio"] for d in data_points) / len(data_points) if data_points else None
            }
        }