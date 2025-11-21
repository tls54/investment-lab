# Crypto Currency Error Handling - Edge Cases

## Overview

What happens when users request invalid or unsupported currencies for crypto? Let's trace through both scenarios.

---

## Scenario 1: Invalid/Misspelled Currency

### Example Request
```bash
GET /api/price/BTC?asset_type=crypto&currency=XYZ
```

### Step-by-Step Flow

**Step 1: API Receives Request**
```python
# prices.py:68-72
symbol = "BTC"
asset_type = AssetType.CRYPTO
currency = "XYZ"  # Invalid currency code
```

**Step 2: Symbol Normalization**
```python
# yfinance_fetcher.py:53-84
def _normalize_crypto_symbol(symbol, asset_type, currency):
    symbol = "BTC".upper().strip()      # "BTC"
    currency = "XYZ".upper().strip()    # "XYZ"

    # Since asset_type == CRYPTO
    return f"{symbol}-{currency}"       # Returns "BTC-XYZ"
```

**Result:** `normalized_symbol = "BTC-XYZ"`

**Step 3: Fetch from yfinance**
```python
# yfinance_fetcher.py:109-110
ticker = yf.Ticker("BTC-XYZ")
info = ticker.info
```

**What happens:** yfinance attempts to fetch data for `BTC-XYZ` pair.

**Step 4: yfinance Response**

yfinance returns an empty or minimal `info` dict:
```python
info = {}  # or {'symbol': 'BTC-XYZ', ...} with no price data
```

**Step 5: Validation Check**
```python
# yfinance_fetcher.py:113-114
if not info or 'regularMarketPrice' not in info:
    raise SymbolNotFoundError(original_symbol, self.name)
    #                         ^^^^^^^^^^^^^^^ "BTC" (not "BTC-XYZ")
```

**Important:** Error uses `original_symbol` ("BTC"), not `normalized_symbol` ("BTC-XYZ")

**Step 6: Error Propagates to API**
```python
# prices.py:123-125
except SymbolNotFoundError as e:
    raise HTTPException(
        status_code=404,
        detail=f"Symbol '{symbol}' not found"
    )
```

### Final Response

**HTTP Status:** `404 Not Found`

**Response Body:**
```json
{
  "detail": "Symbol 'BTC' not found"
}
```

### Problem with Current Error Message

**User sees:**
> "Symbol 'BTC' not found"

**User thinks:**
> "But BTC exists! Why can't you find it?"

**Reality:**
> The `BTC-XYZ` pair doesn't exist in yfinance

**Better error message would be:**
> "Symbol 'BTC' not found with currency 'XYZ'. Try USD, EUR, GBP, or JPY."

---

## Scenario 2: Real Currency, Not Supported by yfinance

### Example Request
```bash
GET /api/price/BTC?asset_type=crypto&currency=INR
```

**INR = Indian Rupee** (valid ISO 4217 currency code)

### Step-by-Step Flow

**Step 1-2: Same as Scenario 1**
```python
normalized_symbol = "BTC-INR"
```

**Step 3: Fetch from yfinance**
```python
ticker = yf.Ticker("BTC-INR")
info = ticker.info
```

**Step 4: yfinance Response**

This depends on yfinance's data availability:

**Case A: yfinance has BTC-INR** (unlikely but possible)
```python
info = {
    'regularMarketPrice': 3750000.50,
    'currency': 'INR',
    'quoteType': 'CRYPTOCURRENCY',
    ...
}
```
✅ **Works!** Returns price in INR.

**Case B: yfinance doesn't have BTC-INR** (more likely)
```python
info = {}  # or minimal data without price
```

**Step 5: Same validation failure**
```python
if not info or 'regularMarketPrice' not in info:
    raise SymbolNotFoundError("BTC", "yfinance")
```

### Final Response

**Same as Scenario 1:**

**HTTP Status:** `404 Not Found`

**Response Body:**
```json
{
  "detail": "Symbol 'BTC' not found"
}
```

### The User Experience Problem

**User Request:**
```bash
GET /api/price/BTC?asset_type=crypto&currency=INR
```

**Error Response:**
```json
{"detail": "Symbol 'BTC' not found"}
```

**User Confusion:**
1. "But I can get BTC in USD, why not INR?"
2. "Is BTC misspelled? Did I do something wrong?"
3. "Does this API not support BTC?"

**Real Issue:** The API supports BTC, but not in INR. yfinance doesn't have the BTC-INR pair.

---

## Current Behavior Summary

### Both Scenarios Result in Same Error

| Scenario | Normalized Symbol | yfinance Result | Error | HTTP Status |
|----------|-------------------|-----------------|-------|-------------|
| Invalid currency (`XYZ`) | `BTC-XYZ` | No data | `Symbol 'BTC' not found` | 404 |
| Unsupported currency (`INR`) | `BTC-INR` | No data | `Symbol 'BTC' not found` | 404 |

### Why This Happens

```python
# yfinance_fetcher.py:132
symbol=original_symbol  # Always uses "BTC", not "BTC-INR"
```

The error message references the **user's input** (`"BTC"`), not the **normalized symbol** (`"BTC-INR"`).

**Pros:**
- Cleaner error message
- Doesn't expose internal implementation details

**Cons:**
- Doesn't explain why the valid symbol failed
- No guidance on what currencies are supported

---

## What Should Happen Instead?

### Improved Error Handling Strategy

#### Option 1: More Informative Error Message

**Current:**
```json
{"detail": "Symbol 'BTC' not found"}
```

**Improved:**
```json
{
  "detail": "Symbol 'BTC' not found with currency 'INR'",
  "suggestion": "Try supported currencies: USD, EUR, GBP, JPY, AUD, CAD",
  "attempted_pair": "BTC-INR"
}
```

#### Option 2: Validate Currency Before Fetching

```python
def _normalize_crypto_symbol(
    self,
    symbol: str,
    asset_type: Optional[AssetType] = None,
    currency: str = "USD"
) -> str:
    # Validate currency is in known supported list
    SUPPORTED_CURRENCIES = {
        "USD", "EUR", "GBP", "JPY", "AUD", "CAD",
        "CHF", "HKD", "SGD", "KRW"
    }

    currency = currency.upper().strip()

    if currency not in SUPPORTED_CURRENCIES:
        raise UnsupportedCurrencyError(
            currency,
            f"Currency '{currency}' is not supported. "
            f"Supported: {', '.join(SUPPORTED_CURRENCIES)}"
        )

    # Continue with normalization...
```

**Response:**
```json
{
  "detail": "Currency 'INR' is not supported. Supported: USD, EUR, GBP, JPY, AUD, CAD, CHF, HKD, SGD, KRW"
}
```

**Pros:**
- Immediate, clear feedback
- Guides user to working currencies
- No wasted API call to yfinance

**Cons:**
- Hardcoded list may become stale
- yfinance might add new pairs we don't know about

#### Option 3: Try Fallback to Triangular Conversion

```python
async def fetch_price_with_fallback(
    self,
    symbol: str,
    asset_type: AssetType,
    currency: str = "USD"
) -> Price:
    try:
        # Try direct pair first
        return await self.fetch_price(symbol, asset_type, currency)

    except SymbolNotFoundError:
        # If direct pair fails, try triangular conversion
        # BTC-INR = BTC-USD × USD-INR

        if currency != "USD":
            logger.info(
                f"Direct pair {symbol}-{currency} not found, "
                f"attempting triangular conversion via USD"
            )

            # Fetch BTC-USD
            btc_usd = await self.fetch_price(symbol, asset_type, "USD")

            # Fetch USD-INR forex rate
            usd_inr = await self.fetch_forex_rate("USD", currency)

            # Calculate BTC-INR
            btc_inr_price = btc_usd.price * usd_inr

            return Price(
                symbol=symbol,
                price=btc_inr_price,
                currency=currency,
                # ... other fields
                source="yfinance (triangular)"
            )

        # If already USD or conversion fails, re-raise
        raise
```

**Pros:**
- Supports ANY currency with USD pair
- Automatic fallback, transparent to user
- More currencies work "magically"

**Cons:**
- Requires forex rate API (Alpha Vantage has this)
- Two API calls instead of one
- Slight inaccuracy from spreads

---

## Testing These Scenarios

### Test Case 1: Invalid Currency

```python
@pytest.mark.asyncio
async def test_invalid_currency(fetcher):
    """Test that invalid currency returns meaningful error."""
    with pytest.raises(SymbolNotFoundError) as exc_info:
        await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="XYZ")

    error_msg = str(exc_info.value)

    # Current behavior
    assert "BTC" in error_msg

    # Ideal behavior (not yet implemented)
    # assert "XYZ" in error_msg
    # assert "supported currencies" in error_msg.lower()
```

### Test Case 2: Real but Unsupported Currency

```python
@pytest.mark.asyncio
async def test_unsupported_real_currency(fetcher):
    """
    Test behavior with valid currency code that yfinance doesn't support.

    NOTE: This might pass if yfinance adds support for the pair!
    """
    # Try a real currency unlikely to be supported
    with pytest.raises(SymbolNotFoundError) as exc_info:
        await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency="INR")

    # Should indicate currency-specific issue
    # (not yet implemented)
```

### Test Case 3: Supported Currency (Baseline)

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "JPY"])
async def test_supported_currency_works(fetcher, currency):
    """Verify known good currencies work."""
    price = await fetcher.fetch_price("BTC", AssetType.CRYPTO, currency=currency)

    assert price is not None
    assert price.price > 0
    assert price.currency == currency
```

---

## Recommendations

### Short-term (Quick Fix)

**Update error message to include currency context:**

```python
# yfinance_fetcher.py:114
if not info or 'regularMarketPrice' not in info:
    # Include currency in error for crypto
    if asset_type == AssetType.CRYPTO and currency != "USD":
        raise SymbolNotFoundError(
            f"{original_symbol} with currency {currency}",
            self.name
        )
    else:
        raise SymbolNotFoundError(original_symbol, self.name)
```

**Error becomes:**
```json
{
  "detail": "Symbol 'BTC with currency INR' not found"
}
```

Still not perfect, but better than "Symbol 'BTC' not found".

### Medium-term (Better)

**Add currency validation with helpful message:**

1. Maintain list of known working currencies
2. Validate before API call
3. Return specific error with suggestions

### Long-term (Best)

**Implement triangular conversion:**

1. Try direct pair first
2. If fails and currency != USD, try via USD
3. Cache forex rates for efficiency
4. Document behavior in API docs

---

## Current Code References

- **Error raised:** `backend/src/price_service/fetchers/yfinance_fetcher.py:114`
- **Error caught:** `backend/src/api/routers/prices.py:123-125`
- **SymbolNotFoundError:** `backend/src/price_service/models.py:144-149`
- **Normalization:** `backend/src/price_service/fetchers/yfinance_fetcher.py:53-84`

---

*Last Updated: 2025-11-20*
