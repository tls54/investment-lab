"""
Denomination converter for pricing assets in terms of other assets.

This module allows pricing any asset in terms of any other asset.
Example: AAPL priced in BTC, SPY priced in Gold, etc.
"""

from typing import Optional, List, Tuple
from datetime import datetime
import logging

from .models import Price, HistoricalPrice, AssetType
from .fetchers import AlphaVantageFetcher, YFinanceFetcher


logger = logging.getLogger(__name__)


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

        # Validate matching currencies for accurate conversion
        if asset_price.currency != denom_price.currency:
            raise ValueError(
                f"Currency mismatch: {asset_symbol} is priced in {asset_price.currency} "
                f"but {denomination_symbol} is priced in {denom_price.currency}. "
                f"Cross-currency conversion is not yet supported. Please ensure both assets use the same currency."
            )
        
        # Calculate ratio
        # How many denomination units equals one asset unit?
        ratio = asset_price.price / denom_price.price
        inverse_ratio = denom_price.price / asset_price.price
        
        logger.info(
            f"1 {asset_symbol} = {ratio:.6f} {denomination_symbol} "
            f"({asset_price.price} / {denom_price.price})"
        )
        
        return {
            "asset_symbol": asset_symbol,
            "denomination_symbol": denomination_symbol,
            "ratio": ratio,
            "asset_price_usd": asset_price.price,
            "denomination_price_usd": denom_price.price,
            "asset_currency": asset_price.currency,
            "denomination_currency": denom_price.currency,
            "timestamp": asset_price.timestamp.isoformat(),
            "inverse_ratio": inverse_ratio,
            "interpretation": f"1 {asset_symbol} = {ratio:.6f} {denomination_symbol}",
            "inverse_interpretation": f"1 {denomination_symbol} = {inverse_ratio:.2f} {asset_symbol}"
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

        # Validate matching currencies for accurate conversion
        if asset_history.prices and denom_history.prices:
            asset_curr = asset_history.prices[0].currency
            denom_curr = denom_history.prices[0].currency
            if asset_curr != denom_curr:
                raise ValueError(
                    f"Currency mismatch: {asset_symbol} is priced in {asset_curr} "
                    f"but {denomination_symbol} is priced in {denom_curr}. "
                    f"Cross-currency conversion is not yet supported. Please ensure both assets use the same currency."
                )
        
        # Match up timestamps and calculate ratios
        # We'll use the asset timestamps as the reference
        data_points = []
        
        # Create a dict for quick denomination price lookup
        denom_prices = {
            p.timestamp.date(): p.price 
            for p in denom_history.prices
        }
        
        for asset_price_obj in asset_history.prices:
            date = asset_price_obj.timestamp.date()
            
            # Find matching denomination price
            if date in denom_prices:
                denom_price = denom_prices[date]
                ratio = asset_price_obj.price / denom_price
                
                data_points.append({
                    "timestamp": asset_price_obj.timestamp.isoformat(),
                    "date": date.isoformat(),
                    "ratio": ratio,
                    "asset_price_usd": asset_price_obj.price,
                    "denomination_price_usd": denom_price,
                    "inverse_ratio": denom_price / asset_price_obj.price
                })
        
        logger.info(f"Generated {len(data_points)} conversion data points")
        
        return {
            "asset_symbol": asset_symbol,
            "denomination_symbol": denomination_symbol,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "interval": interval,
            "count": len(data_points),
            "data": data_points,
            "summary": {
                "min_ratio": min(d["ratio"] for d in data_points) if data_points else None,
                "max_ratio": max(d["ratio"] for d in data_points) if data_points else None,
                "avg_ratio": sum(d["ratio"] for d in data_points) / len(data_points) if data_points else None
            }
        }