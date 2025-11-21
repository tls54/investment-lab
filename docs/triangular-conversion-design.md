# Triangular Conversion Design

## Goal

Support crypto pricing in any currency by calculating via USD when direct pairs aren't available.

## Strategy: Try Direct First, Fallback to Triangular

```
User requests: BTC in INR
    ↓
Try: BTC-INR (direct pair)
    ↓
Not found? → Try triangular conversion
    ↓
Fetch: BTC-USD (usually available)
Fetch: USD-INR forex rate (usually available)
Calculate: BTC-INR = BTC-USD × USD-INR
    ↓
Return result (mark as "triangular" in metadata)
```

## Implementation Design

### 1. Refactor fetch_price into Two Methods

```python
async def fetch_price(symbol, asset_type, currency):
    """Public method - tries direct first, falls back to triangular"""
    try:
        # Try direct pair first (e.g., BTC-INR)
        return await self._fetch_price_direct(symbol, asset_type, currency)

    except SymbolNotFoundError:
        # Direct pair failed - try triangular if applicable
        if self._should_try_triangular(asset_type, currency):
            return await self._fetch_price_triangular(symbol, asset_type, currency)
        else:
            raise  # Re-raise if triangular not applicable

async def _fetch_price_direct(symbol, asset_type, currency):
    """Current implementation - fetch direct pair from yfinance"""
    # Existing code (lines 103-154)
    ...

async def _fetch_price_triangular(symbol, asset_type, currency):
    """Triangular conversion: Crypto-Currency = Crypto-USD × USD-Currency"""
    # New implementation
    ...
```

### 2. Decision Logic: When to Try Triangular?

```python
def _should_try_triangular(
    self,
    asset_type: Optional[AssetType],
    currency: str
) -> bool:
    """
    Determine if triangular conversion should be attempted.

    Triangular conversion is applicable when:
    1. Asset is crypto (stocks/ETFs don't work this way)
    2. Currency is not USD (avoid infinite loop)
    3. Feature is enabled (allow disabling if needed)

    Returns:
        True if triangular conversion should be tried
    """
    # Only for crypto
    if asset_type != AssetType.CRYPTO:
        return False

    # Don't try if already USD (would create loop)
    if currency.upper() == "USD":
        return False

    # Could add feature flag here
    # if not self.enable_triangular:
    #     return False

    return True
```

### 3. Forex Rate Fetching

yfinance supports forex rates using special symbols:
- Format: `{FROM}{TO}=X`
- Example: `USDINR=X` for USD → INR rate
- Example: `EURUSD=X` for EUR → USD rate

```python
async def _fetch_forex_rate(
    self,
    from_currency: str,
    to_currency: str
) -> float:
    """
    Fetch forex exchange rate.

    Args:
        from_currency: Source currency (e.g., "USD")
        to_currency: Target currency (e.g., "INR")

    Returns:
        Exchange rate (e.g., 83.12 for USD to INR)

    Example:
        rate = await _fetch_forex_rate("USD", "INR")
        # rate = 83.12 (1 USD = 83.12 INR)
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
            raise ValueError(
                f"Forex rate {from_currency}/{to_currency} not available"
            )

        logger.info(f"Forex rate {from_currency}/{to_currency}: {rate}")
        return float(rate)

    except Exception as e:
        logger.error(f"Failed to fetch forex rate {forex_symbol}: {e}")
        raise APIError(
            self.name,
            0,
            f"Unable to fetch forex rate {from_currency}/{to_currency}: {e}"
        )
```

### 4. Triangular Conversion Implementation

```python
async def _fetch_price_triangular(
    self,
    symbol: str,
    asset_type: AssetType,
    currency: str
) -> Price:
    """
    Fetch price using triangular conversion via USD.

    Example:
        BTC-INR = BTC-USD × USD-INR

    Args:
        symbol: Crypto symbol (e.g., "BTC")
        asset_type: Should be CRYPTO
        currency: Target currency (e.g., "INR")

    Returns:
        Price object with calculated price in target currency
    """
    logger.info(
        f"Attempting triangular conversion: {symbol}-{currency} "
        f"via {symbol}-USD × USD-{currency}"
    )

    try:
        # Step 1: Fetch crypto price in USD
        # This calls _fetch_price_direct with currency="USD"
        crypto_usd = await self._fetch_price_direct(
            symbol,
            asset_type,
            "USD"
        )

        # Step 2: Fetch forex rate USD → target currency
        forex_rate = await self._fetch_forex_rate("USD", currency)

        # Step 3: Calculate price in target currency
        calculated_price = crypto_usd.price * forex_rate

        logger.info(
            f"Triangular conversion successful: "
            f"{symbol} ${crypto_usd.price} × {forex_rate} "
            f"= {calculated_price} {currency}"
        )

        # Step 4: Build Price object with calculated values
        return Price(
            symbol=symbol,
            asset_type=asset_type,
            price=calculated_price,
            timestamp=datetime.now(),
            currency=currency,
            volume=crypto_usd.volume,  # Volume from USD pair
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
```

## Error Handling

### Case 1: Direct Pair Exists
```
Request: BTC in EUR
    ↓
Try: BTC-EUR → ✓ Success
    ↓
Return: Direct result
```

### Case 2: Direct Pair Fails, Triangular Succeeds
```
Request: BTC in INR
    ↓
Try: BTC-INR → ✗ Not found
    ↓
Try: BTC-USD → ✓ Success ($45,000)
Try: USD-INR → ✓ Success (83.12)
Calculate: 45,000 × 83.12 = 3,740,400
    ↓
Return: Triangular result (marked as "triangular" in source)
```

### Case 3: Direct Fails, Triangular Fails
```
Request: BTC in XYZ (invalid)
    ↓
Try: BTC-XYZ → ✗ Not found
    ↓
Try: BTC-USD → ✓ Success
Try: USD-XYZ → ✗ Not found
    ↓
Raise: SymbolNotFoundError("BTC with currency XYZ")
```

### Case 4: Direct Fails, Triangular Not Applicable
```
Request: BTC in USD (already USD)
    ↓
Try: BTC-USD → ✗ Not found (unusual, but possible)
    ↓
Check: Should try triangular? → No (currency is USD)
    ↓
Raise: SymbolNotFoundError("BTC")
```

## Infinite Loop Prevention

**Question:** What if BTC-USD also fails?

**Answer:** We only try triangular when `currency != "USD"`, so:
1. Direct: BTC-INR fails
2. Triangular: Tries BTC-USD
3. If BTC-USD fails, it raises error (doesn't try triangular again)

**Code:**
```python
def _should_try_triangular(self, asset_type, currency):
    # This prevents infinite loop
    if currency.upper() == "USD":
        return False
    return asset_type == AssetType.CRYPTO
```

## Performance Considerations

### 1. API Call Count

**Direct pair exists:**
- 1 call (BTC-EUR)

**Triangular needed:**
- 2 calls (BTC-USD + USD-INR)

### 2. Caching

**Forex rates change slowly** → Cache for longer

```python
# In _fetch_forex_rate
# Could cache forex rates for 5-10 minutes
# vs crypto prices cached for 1-5 seconds
```

### 3. Latency

**Direct:** ~200ms
**Triangular:** ~400ms (2 API calls)

Still acceptable for most use cases.

## User Experience

### API Response Transparency

**Direct Pair:**
```json
{
  "symbol": "BTC",
  "price": 3750000.50,
  "currency": "INR",
  "source": "yfinance"
}
```

**Triangular Conversion:**
```json
{
  "symbol": "BTC",
  "price": 3740400.00,
  "currency": "INR",
  "source": "yfinance (triangular)",
  "calculation": {
    "method": "triangular",
    "via": "USD",
    "btc_usd": 45000.00,
    "usd_inr": 83.12
  }
}
```

Users can see it was calculated, not a direct quote.

## Historical Data

**Same logic applies:**

```python
async def fetch_historical(..., currency):
    try:
        return await self._fetch_historical_direct(...)
    except SymbolNotFoundError:
        if self._should_try_triangular(asset_type, currency):
            return await self._fetch_historical_triangular(...)
        raise

async def _fetch_historical_triangular(symbol, start, end, currency):
    # Fetch historical BTC-USD
    hist_usd = await self._fetch_historical_direct(symbol, start, end, "USD")

    # Fetch historical USD-INR rates for same dates
    forex_hist = await self._fetch_historical_forex("USD", currency, start, end)

    # Match up dates and multiply
    for price_point in hist_usd.prices:
        date = price_point.timestamp.date()
        forex_rate = forex_hist[date]
        price_point.price *= forex_rate
        price_point.currency = currency

    return hist_usd
```

## Testing Strategy

```python
# Test that direct pair is preferred
async def test_direct_pair_preferred():
    """If BTC-EUR exists, don't use triangular."""
    price = await fetcher.fetch_price("BTC", CRYPTO, "EUR")
    assert price.source == "yfinance"  # Not "yfinance (triangular)"

# Test triangular fallback
async def test_triangular_fallback():
    """If direct pair fails, try triangular."""
    price = await fetcher.fetch_price("BTC", CRYPTO, "INR")
    # Should succeed via triangular
    assert price is not None
    assert price.currency == "INR"
    assert "triangular" in price.source

# Test invalid currency
async def test_both_fail():
    """If both direct and triangular fail, raise error."""
    with pytest.raises(SymbolNotFoundError):
        await fetcher.fetch_price("BTC", CRYPTO, "XYZ")
```

## Migration Path

### Phase 1: Implement (No Breaking Changes)
- Add new methods
- Keep existing behavior as fallback
- Add feature flag to enable/disable

### Phase 2: Test
- Test with known unsupported currencies
- Verify forex rates are accurate
- Check performance impact

### Phase 3: Document
- Update API docs
- Add examples
- Note limitations

### Phase 4: Enable by Default
- Monitor error rates
- Collect user feedback

## Limitations

1. **Accuracy:** Triangular conversion has small errors due to:
   - Different update times
   - Bid/ask spreads
   - yfinance data delays

2. **Forex Coverage:** Not all currency pairs available
   - Most major currencies work (INR, CNY, KRW, etc.)
   - Exotic pairs might fail

3. **Performance:** 2x API calls vs 1

4. **Stocks/ETFs:** This only works for crypto
   - AAPL-INR doesn't make sense (Apple doesn't trade in India)
   - Stock prices are exchange-specific

---

*Ready to implement!*
