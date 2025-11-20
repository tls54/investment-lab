"""
Price endpoints for the Investment Lab API.

This module handles all price-related operations:
- Fetching current prices
- Fetching historical prices
- Supporting multiple data sources
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

# Import configuration
from ...core.config import settings

# Import our fetchers
from ...price_service.fetchers import AlphaVantageFetcher, YFinanceFetcher
from ...price_service.models import AssetType, SymbolNotFoundError, RateLimitError, APIError
from ...price_service.converter import DenominationConverter


# Create a router
router = APIRouter()

# Initialize fetchers using settings
fetchers = {
    "alpha_vantage": AlphaVantageFetcher(
        api_key=settings.alpha_vantage_api_key
    ) if settings.alpha_vantage_api_key else None,
    "yfinance": YFinanceFetcher()
}

converter = DenominationConverter(fetchers)


def get_fetcher(asset_type: Optional[AssetType], source: Optional[str]):
    """
    Select the appropriate fetcher based on asset type and requested source.

    Args:
        asset_type: Type of asset (STOCK, CRYPTO, etc.)
        source: Requested data source (optional)

    Returns:
        Appropriate fetcher instance

    Raises:
        HTTPException: If no suitable fetcher is available
    """
    # If user specified a source, try to use it
    if source:
        fetcher = fetchers.get(source)
        if fetcher is None:
            raise HTTPException(status_code=400, detail=f"Source '{source}' not available")
        return fetcher

    # Auto-select based on asset type
    # yfinance now supports stocks, ETFs, and crypto (via -USD suffix)
    return fetchers["yfinance"]


# ============================================================================
# ENDPOINT 1: Get Current Price
# ============================================================================

@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    asset_type: Optional[AssetType] = Query(None, description="Type of asset (stock, crypto, etc.)"),
    source: Optional[str] = Query(None, description="Data source (alpha_vantage, yfinance)"),
    currency: str = Query("USD", description="Currency for crypto prices (e.g., USD, EUR, GBP)")
):
    """
    Get the current price for a symbol.

    **Examples:**
    - `/api/price/AAPL` - Get Apple stock price
    - `/api/price/BTC?asset_type=crypto` - Get Bitcoin price
    - `/api/price/BTC?asset_type=crypto&currency=EUR` - Get Bitcoin price in EUR
    - `/api/price/MSFT?source=alpha_vantage` - Get Microsoft from specific source

    **Parameters:**
    - `symbol`: The asset symbol (e.g., AAPL, BTC, MSFT)
    - `asset_type`: Optional. Helps select the right data source.
    - `source`: Optional. Force a specific data source.
    - `currency`: Currency for crypto prices (default: USD). Examples: EUR, GBP, JPY

    **Returns:**
    - JSON object with price data

    **Errors:**
    - 404: Symbol not found
    - 429: Rate limit exceeded
    - 500: API error
    """
    try:
        # Get the appropriate fetcher
        fetcher = get_fetcher(asset_type, source)

        # Fetch the price (this is async, so we await it)
        price = await fetcher.fetch_price(symbol, asset_type, currency=currency)
        
        # Convert to dict for JSON response
        # Pydantic models have .dict() method
        return {
            "symbol": price.symbol,
            "price": price.price,
            "currency": price.currency,
            "timestamp": price.timestamp.isoformat(),
            "source": price.source,
            "volume": price.volume,
            "asset_type": price.asset_type.value,
            # Optional fields
            "bid": price.bid,
            "ask": price.ask,
            "open": price.open,
            "high": price.high_24h,
            "low": price.low_24h,
            "close": price.close
        }
        
    except SymbolNotFoundError as e:
        # Return 404 when symbol doesn't exist
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    
    except RateLimitError as e:
        # Return 429 when rate limit hit
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {e.retry_after} seconds"
        )
    
    except APIError as e:
        # Return 500 for other API errors
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# ENDPOINT 2: Get Historical Prices
# ============================================================================

@router.get("/price/{symbol}/history")
async def get_historical_prices(
    symbol: str,
    # Option 1: Simple "days" parameter
    days: Optional[int] = Query(7, ge=1, le=365, description="Number of days of history (1–365, alternative to start/end)"),
    # Option 2: Custom date range
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Time interval (1d, 1h, 5m)"),
    asset_type: Optional[AssetType] = Query(None, description="Type of asset"),
    source: Optional[str] = Query(None, description="Data source"),
    currency: str = Query("USD", description="Currency for crypto prices (e.g., USD, EUR, GBP)")
):
    """
    Get historical prices for a symbol.

    You can specify the time range in two ways:

    **Option 1 (default):**
    - `/api/price/AAPL/history?days=7` → Last 7 days
    - `/api/price/BTC/history?days=30&interval=1h` → Hourly for 30 days
    - `/api/price/BTC/history?days=30&currency=EUR` → Bitcoin in EUR for 30 days

    **Option 2 (custom dates):**
    - `/api/price/AAPL/history?start_date=2025-01-01&end_date=2025-06-01`
    - `/api/price/ETH/history?start_date=2025-04-01` (defaults end_date to today)
    - `/api/price/ETH/history?start_date=2025-04-01&currency=GBP` → Ethereum in GBP

    **Parameters:**
    - `symbol`: Asset symbol
    - `days`: Days of history (alternative to custom range)
    - `start_date`, `end_date`: Optional date range (YYYY-MM-DD)
    - `interval`: Time interval (default: 1d)
    - `asset_type`, `source`: Optional filters
    - `currency`: Currency for crypto prices (default: USD). Examples: EUR, GBP, JPY
    """
    try:
        # Determine time window
        if start_date or end_date:
            # Custom date range mode
            if start_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid start_date format (YYYY-MM-DD required)")
            else:
                start = datetime.now() - timedelta(days=7)

            if end_date:
                try:
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid end_date format (YYYY-MM-DD required)")
            else:
                end = datetime.now()

            if start >= end:
                raise HTTPException(status_code=400, detail="start_date must be before end_date")

            days_diff = (end - start).days
            if days_diff > 365:
                raise HTTPException(status_code=400, detail="Date range cannot exceed 365 days")

        else:
            # Default to "days" mode
            end = datetime.now()
            start = end - timedelta(days=days or 7)

        # Fetch data
        fetcher = get_fetcher(asset_type, source)
        historical = await fetcher.fetch_historical(symbol, start, end, interval, asset_type, currency=currency)

        return {
            "symbol": historical.symbol,
            "asset_type": historical.asset_type.value,
            "start_date": historical.start_date.isoformat(),
            "end_date": historical.end_date.isoformat(),
            "interval": historical.interval,
            "count": len(historical.prices),
            "prices": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "price": p.price,
                    "volume": p.volume,
                    "open": p.open,
                    "high": p.high_24h,
                    "low": p.low_24h,
                    "close": p.close
                }
                for p in historical.prices
            ]
        }

    except SymbolNotFoundError:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Retry after {e.retry_after} seconds")
    except APIError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ============================================================================
# ENDPOINT 4: Convert Price to Denomination
# ============================================================================

@router.get("/convert/{asset}/{denomination}")
async def convert_price(
    asset: str,
    denomination: str,
    asset_type: Optional[AssetType] = Query(None, description="Type of asset"),
    denomination_type: Optional[AssetType] = Query(None, description="Type of denomination"),
    asset_currency: str = Query("USD", description="Currency for crypto asset (e.g., USD, EUR, GBP)"),
    denomination_currency: str = Query("USD", description="Currency for crypto denomination (e.g., USD, EUR, GBP)")
):
    """
    Convert asset price to a different denomination.

    This is the killer feature - price anything in terms of anything!

    **Examples:**
    - `/api/convert/AAPL/BTC` - Apple priced in Bitcoin
    - `/api/convert/SPY/GLD` - S&P 500 priced in Gold ETF
    - `/api/convert/ETH/AAPL` - Ethereum priced in Apple shares
    - `/api/convert/MSFT/BTC?asset_type=stock&denomination_type=crypto`
    - `/api/convert/BTC/ETH?asset_currency=EUR&denomination_currency=EUR` - Bitcoin in terms of Ethereum (both in EUR)

    **Parameters:**
    - `asset`: Symbol of asset to price (e.g., AAPL)
    - `denomination`: Symbol to price it in (e.g., BTC)
    - `asset_type`: Optional asset type
    - `denomination_type`: Optional denomination type
    - `asset_currency`: Currency for crypto asset (default: USD)
    - `denomination_currency`: Currency for crypto denomination (default: USD)

    **Important:**
    - Both assets must be priced in the same currency for accurate conversion
    - Cross-currency conversion is not yet supported

    **Returns:**
    - Conversion ratio and both prices in the specified currency
    - Interpretation in both directions

    **Use Cases:**
    - Compare assets without USD bias
    - Track relative performance
    - Find arbitrage opportunities
    - Hedge calculations
    """
    try:
        result = await converter.convert(
            asset, denomination, asset_type, denomination_type,
            asset_currency=asset_currency,
            denomination_currency=denomination_currency
        )
        return result
        
    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {e.retry_after} seconds"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


# ============================================================================
# ENDPOINT 5: Convert Historical Prices to Denomination
# ============================================================================

# Replace the convert_historical_prices endpoint in prices.py with this:

@router.get("/convert/{asset}/{denomination}/history")
async def convert_historical_prices(
    asset: str,
    denomination: str,
    # Option 1: Use days parameter (simple)
    days: Optional[int] = Query(None, ge=1, le=365, description="Number of days of history (alternative to start/end)"),
    # Option 2: Use exact dates (flexible)
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    interval: str = Query("1d", description="Time interval"),
    asset_type: Optional[AssetType] = Query(None, description="Type of asset"),
    denomination_type: Optional[AssetType] = Query(None, description="Type of denomination"),
    asset_currency: str = Query("USD", description="Currency for crypto asset (e.g., USD, EUR, GBP)"),
    denomination_currency: str = Query("USD", description="Currency for crypto denomination (e.g., USD, EUR, GBP)")
):
    """
    Convert historical asset prices to a denomination.
    
    Shows how the ratio between two assets has changed over time.
    
    **You can specify the time range in two ways:**
    
    **Option 1: Use days parameter (simple)**
    - `/api/convert/AAPL/BTC/history?days=7` - Last 7 days
    - `/api/convert/AAPL/BTC/history?days=30` - Last 30 days
    
    **Option 2: Use exact dates (flexible)**
    - `/api/convert/AAPL/BTC/history?start_date=2025-01-01&end_date=2025-06-01`
    - `/api/convert/AAPL/BTC/history?start_date=2024-11-01&end_date=2025-11-01`
    
    **Examples:**
    - `/api/convert/AAPL/BTC/history?days=7` - Last 7 days
    - `/api/convert/SPY/GLD/history?start_date=2025-01-01&end_date=2025-11-08`
    - `/api/convert/ETH/AAPL/history?start_date=2024-06-01&end_date=2024-12-31&interval=1d`
    
    **Parameters:**
    - `asset`: Asset symbol
    - `denomination`: Denomination symbol
    - `days`: Number of days back from today (1-365) - OR use start_date/end_date
    - `start_date`: Start date in YYYY-MM-DD format - OR use days
    - `end_date`: End date in YYYY-MM-DD format (defaults to today) - OR use days
    - `interval`: Time interval (default: 1d)
    - `asset_type`: Optional asset type
    - `denomination_type`: Optional denomination type
    
    **Note:** Either use `days` OR `start_date/end_date`, not both.
    If both provided, `start_date/end_date` takes precedence.
    
    **Returns:**
    - Historical conversion ratios
    - Both USD prices at each point
    - Summary statistics (min, max, avg)
    """
    try:
        # Determine date range
        # Priority: start_date/end_date > days > default (7 days)
        
        if start_date or end_date:
            # Option 2: Exact dates
            if start_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use YYYY-MM-DD (e.g., 2025-01-15)"
                    )
            else:
                # If only end_date provided, default to 7 days before end
                start = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=7)
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid end_date format. Use YYYY-MM-DD (e.g., 2025-11-08)"
                    )
            else:
                # If only start_date provided, default to today
                end = datetime.now()
            
            # Validate date range
            if start >= end:
                raise HTTPException(
                    status_code=400,
                    detail="start_date must be before end_date"
                )
            
            # Check if range is too large (prevent abuse)
            days_diff = (end - start).days
            if days_diff > 365:
                raise HTTPException(
                    status_code=400,
                    detail="Date range cannot exceed 365 days"
                )
        
        elif days:
            # Option 1: Days parameter
            end = datetime.now()
            start = end - timedelta(days=days)
        
        else:
            # Default: Last 7 days
            end = datetime.now()
            start = end - timedelta(days=7)
        
        # Fetch and convert
        result = await converter.convert_historical(
            asset, denomination, start, end, interval,
            asset_type, denomination_type,
            asset_currency=asset_currency,
            denomination_currency=denomination_currency
        )
        return result
        
    except SymbolNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except RateLimitError as e:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Retry after {e.retry_after} seconds"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")