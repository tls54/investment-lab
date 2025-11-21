# Crypto Currency Logic - How It Works

## Overview

The system allows pricing cryptocurrencies in multiple fiat currencies (USD, EUR, GBP, JPY, etc.) by intelligently transforming user requests into yfinance-compatible symbols.

---

## The Flow (Step by Step)

### Example: Get Bitcoin price in Euros

**User Request:**
```bash
GET /api/price/BTC?asset_type=crypto&currency=EUR
```

### Step 1: API Endpoint Receives Request

**File:** `backend/src/api/routers/prices.py:67-72`

```python
@router.get("/price/{symbol}")
async def get_price(
    symbol: str,                          # "BTC"
    asset_type: Optional[AssetType],      # AssetType.CRYPTO
    currency: str = Query("USD")          # "EUR"
):
```

**What happens:**
- `symbol` = `"BTC"`
- `asset_type` = `AssetType.CRYPTO`
- `currency` = `"EUR"` (from query parameter)

---

### Step 2: API Calls Fetcher

**File:** `backend/src/api/routers/prices.py:102`

```python
# Fetch the price (pass currency to fetcher)
price = await fetcher.fetch_price(symbol, asset_type, currency=currency)
#                                  ^^^^^^  ^^^^^^^^^^  ^^^^^^^^^^^^^^^^
#                                  "BTC"   CRYPTO      "EUR"
```

**What happens:**
- API passes all three parameters to the fetcher
- The `currency` parameter flows through to the yfinance fetcher

---

### Step 3: Symbol Normalization

**File:** `backend/src/price_service/fetchers/yfinance_fetcher.py:53-84`

```python
def _normalize_crypto_symbol(
    self,
    symbol: str,           # "BTC"
    asset_type: Optional[AssetType],  # CRYPTO
    currency: str = "USD"  # "EUR"
) -> str:
    """
    Transform: BTC + EUR → BTC-EUR
    """
    symbol = symbol.upper().strip()    # "BTC"
    currency = currency.upper().strip()  # "EUR"

    # If already has suffix (e.g., "BTC-EUR"), return as-is
    if "-" in symbol and len(symbol.split("-")) == 2:
        return symbol

    # Check if it's crypto (two ways to determine)
    if asset_type == AssetType.CRYPTO or symbol in self.CRYPTO_SYMBOLS:
        return f"{symbol}-{currency}"  # Returns "BTC-EUR"

    return symbol  # For stocks, no suffix needed
```

**Key Logic:**

1. **Already has suffix?** → Return as-is
   ```python
   Input: "BTC-GBP", currency="EUR"
   Output: "BTC-GBP"  # User explicitly specified pair
   ```

2. **Is it crypto?** (Two detection methods)
   - **Method A:** User provided `asset_type=crypto`
   - **Method B:** Symbol is in known crypto list
   ```python
   CRYPTO_SYMBOLS = {
       "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP",
       "DOGE", "ADA", "TRX", "AVAX", "LINK", "DOT", ...
   }
   ```

3. **Build yfinance symbol:**
   ```python
   f"{symbol}-{currency}"  # "BTC" + "EUR" → "BTC-EUR"
   ```

**Examples:**
```python
# Crypto symbols get currency suffix
normalize("BTC", CRYPTO, "EUR")  → "BTC-EUR"
normalize("ETH", CRYPTO, "GBP")  → "ETH-GBP"
normalize("SOL", CRYPTO, "JPY")  → "SOL-JPY"

# Stock symbols stay unchanged
normalize("AAPL", STOCK, "EUR")  → "AAPL"

# Already-suffixed symbols preserved
normalize("BTC-USD", CRYPTO, "EUR")  → "BTC-USD"
```

---

### Step 4: Fetch from yfinance

**File:** `backend/src/price_service/fetchers/yfinance_fetcher.py:109`

```python
async def fetch_price(
    self,
    symbol: str,           # "BTC" (original)
    asset_type: Optional[AssetType],
    currency: str = "USD"  # "EUR"
) -> Price:
    original_symbol = symbol.upper().strip()  # Save "BTC"

    # Transform to yfinance format
    normalized_symbol = self._normalize_crypto_symbol(
        original_symbol,  # "BTC"
        asset_type,       # CRYPTO
        currency          # "EUR"
    )
    # normalized_symbol = "BTC-EUR"

    # Fetch from yfinance
    ticker = yf.Ticker(normalized_symbol)  # yf.Ticker("BTC-EUR")
    info = ticker.info

    current_price = info.get('regularMarketPrice')  # e.g., 45234.50

    # Build response (use ORIGINAL symbol, not normalized)
    price_obj = Price(
        symbol=original_symbol,      # "BTC" (not "BTC-EUR")
        asset_type=asset_type,        # CRYPTO
        price=float(current_price),   # 45234.50
        currency=info.get('currency', 'USD'),  # "EUR" from yfinance
        timestamp=datetime.now(),
        volume=float(info.get('regularMarketVolume', 0)),
        source=self.name  # "yfinance"
    )

    return price_obj
```

**Important Details:**

1. **Symbol Transformation:**
   - **Internal (to yfinance):** `"BTC-EUR"`
   - **External (API response):** `"BTC"`

2. **Currency Comes from yfinance:**
   ```python
   currency=info.get('currency', 'USD')
   ```
   - yfinance tells us what currency the price is in
   - Usually matches what we requested, but yfinance is source of truth

3. **Clean API Responses:**
   - Users see `"BTC"`, not `"BTC-EUR"`
   - Cleaner, more intuitive
   - Currency is separate field

---

### Step 5: API Returns Response

**File:** `backend/src/api/routers/prices.py:106-121`

```python
return {
    "symbol": price.symbol,        # "BTC"
    "price": price.price,          # 45234.50
    "currency": price.currency,    # "EUR"
    "timestamp": price.timestamp.isoformat(),
    "source": price.source,        # "yfinance"
    "volume": price.volume,
    "asset_type": price.asset_type.value  # "crypto"
}
```

**Final Response:**
```json
{
  "symbol": "BTC",
  "price": 45234.50,
  "currency": "EUR",
  "timestamp": "2025-11-20T10:30:00",
  "source": "yfinance",
  "volume": 12345678.0,
  "asset_type": "crypto"
}
```

---

## Historical Data Flow

**Request:**
```bash
GET /api/price/BTC/history?asset_type=crypto&currency=EUR&days=7
```

**Same logic applies:**

1. API receives `currency="EUR"`
2. Passes to `fetcher.fetch_historical(..., currency="EUR")`
3. Symbol normalized: `"BTC"` → `"BTC-EUR"`
4. yfinance fetches historical data for `BTC-EUR`
5. Each price point gets `currency="EUR"`

**Code:** `backend/src/price_service/fetchers/yfinance_fetcher.py:156-229`

```python
async def fetch_historical(
    self,
    symbol: str,           # "BTC"
    start: datetime,
    end: datetime,
    interval: str = "1d",
    asset_type: Optional[AssetType] = None,
    currency: str = "USD"  # "EUR"
) -> HistoricalPrice:
    original_symbol = symbol.upper().strip()

    # Same normalization
    normalized_symbol = self._normalize_crypto_symbol(
        original_symbol, asset_type, currency
    )  # "BTC-EUR"

    # Fetch history
    ticker = yf.Ticker(normalized_symbol)
    hist = ticker.history(start=start, end=end, interval=interval)

    # Convert each row to Price object
    prices = []
    for timestamp, row in hist.iterrows():
        price_obj = Price(
            symbol=original_symbol,  # "BTC"
            price=float(row['Close']),
            currency=currency,       # "EUR"
            timestamp=timestamp.to_pydatetime(),
            ...
        )
        prices.append(price_obj)

    return HistoricalPrice(
        symbol=original_symbol,  # "BTC"
        prices=prices,
        ...
    )
```

---

## Denomination Conversion with Currency

**Request:**
```bash
GET /api/convert/AAPL/BTC?denomination_type=crypto&denomination_currency=EUR
```

**Flow:**

### Step 1: API Endpoint
**File:** `backend/src/api/routers/prices.py:254-262`

```python
@router.get("/convert/{asset}/{denomination}")
async def convert_price(
    asset: str,                    # "AAPL"
    denomination: str,             # "BTC"
    asset_type: Optional[AssetType] = None,
    denomination_type: Optional[AssetType] = None,
    asset_currency: str = Query("USD"),        # "USD" (default)
    denomination_currency: str = Query("USD")  # "EUR" (user specified)
):
```

### Step 2: Converter Fetches Both Prices
**File:** `backend/src/price_service/converter.py:103-104`

```python
# Fetch both assets with their respective currencies
asset_price = await asset_fetcher.fetch_price(
    "AAPL",
    STOCK,
    currency="USD"  # AAPL in USD
)

denom_price = await denom_fetcher.fetch_price(
    "BTC",
    CRYPTO,
    currency="EUR"  # BTC in EUR
)
```

### Step 3: Currency Validation
**File:** `backend/src/price_service/converter.py:107-112`

```python
# CRITICAL: Both must be in same currency!
if asset_price.currency != denom_price.currency:
    raise ValueError(
        f"Currency mismatch: {asset_symbol} is priced in {asset_price.currency} "
        f"but {denomination_symbol} is priced in {denom_price.currency}. "
        f"Cross-currency conversion is not yet supported."
    )
```

**This Fails:**
```bash
# AAPL in USD, BTC in EUR → ERROR
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=EUR
```

**Response:** `500 Internal Server Error`
```json
{
  "detail": "Currency mismatch: AAPL is priced in USD but BTC is priced in EUR. Cross-currency conversion is not yet supported."
}
```

**This Works:**
```bash
# Both in USD
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=USD

# Both in EUR (if AAPL-EUR exists in yfinance)
GET /api/convert/AAPL/BTC?asset_currency=EUR&denomination_currency=EUR
```

### Step 4: Calculate Ratio (if currencies match)
**File:** `backend/src/price_service/converter.py:116`

```python
# Simple division (both prices in same currency)
ratio = asset_price.price / denom_price.price
```

---

## Key Design Decisions

### 1. **Why normalize symbol internally but return original?**

**Problem:**
- yfinance needs `"BTC-EUR"`
- Users expect `"BTC"`

**Solution:**
- Transform on the way in: `"BTC"` → `"BTC-EUR"`
- Transform on the way out: `"BTC-EUR"` → `"BTC"`
- Currency is a separate field

**Benefits:**
- Clean API
- Works with any currency
- Users don't need to know yfinance format

---

### 2. **Why validate matching currencies in converter?**

**Problem:**
```python
# What does this mean?
AAPL_price_usd / BTC_price_eur = ???
```

**This is mathematically incorrect!** You're dividing USD by EUR.

**Correct approach:**
```python
# Both in same currency
AAPL_price_usd / BTC_price_usd = ratio (dimensionless)
AAPL_price_eur / BTC_price_eur = ratio (dimensionless)
```

**Why we validate:**
- Prevents meaningless comparisons
- Forces user to think about currency
- Makes errors obvious

**Future solution (not implemented):**
```python
# Auto-convert to common currency
aapl_usd = 175.50
btc_eur = 45000.00
usd_eur_rate = 0.92

btc_usd = btc_eur / usd_eur_rate  # Convert EUR to USD
ratio = aapl_usd / btc_usd  # Now both in USD
```

---

### 3. **Why maintain CRYPTO_SYMBOLS list?**

**Without asset_type:**
```bash
# User doesn't specify asset_type
GET /api/price/BTC?currency=EUR
```

**How do we know BTC is crypto?**

**Option A:** Check known list
```python
if symbol in CRYPTO_SYMBOLS:
    return f"{symbol}-{currency}"
```

**Option B:** Try to fetch, see what yfinance says
```python
info = yf.Ticker(symbol).info
if info.get('quoteType') == 'CRYPTOCURRENCY':
    ...
```

**We do both!**
- List is faster (no API call)
- Fallback to yfinance for unknown symbols

---

## Edge Cases & Error Handling

### 1. **Symbol Already Has Suffix**
```bash
# User explicitly provides full symbol
GET /api/price/BTC-GBP?asset_type=crypto&currency=EUR
```

**Result:** Uses `BTC-GBP`, ignores `currency=EUR`

**Code logic:**
```python
if "-" in symbol and len(symbol.split("-")) == 2:
    return symbol  # Use as-is
```

---

### 2. **Unsupported Currency**
```bash
GET /api/price/BTC?asset_type=crypto&currency=XYZ
```

**Flow:**
1. Normalize: `"BTC"` → `"BTC-XYZ"`
2. yfinance fetch: `yf.Ticker("BTC-XYZ")`
3. No data found
4. Raise `SymbolNotFoundError`

**Response:** `404 Not Found`
```json
{
  "detail": "Symbol 'BTC' not found"
}
```

---

### 3. **Case Insensitivity**
```bash
GET /api/price/btc?asset_type=crypto&currency=eur
```

**Normalization:**
```python
symbol = symbol.upper().strip()    # "btc" → "BTC"
currency = currency.upper().strip()  # "eur" → "EUR"
return f"{symbol}-{currency}"      # "BTC-EUR"
```

**Works perfectly!**

---

### 4. **Empty or Whitespace Currency**
```bash
GET /api/price/BTC?asset_type=crypto&currency=%20%20
```

**Normalization:**
```python
currency = currency.upper().strip()  # "  " → ""
return f"{symbol}-{currency}"       # "BTC-"
```

**Result:** Invalid symbol `"BTC-"` → Error

**Could improve:**
```python
if not currency or not currency.strip():
    currency = "USD"  # Default fallback
```

---

## Summary: The Full Journey

```
User Request
    ↓
GET /api/price/BTC?asset_type=crypto&currency=EUR
    ↓
API Endpoint (prices.py:68)
    ↓
Extract: symbol="BTC", asset_type=CRYPTO, currency="EUR"
    ↓
Call: fetcher.fetch_price("BTC", CRYPTO, currency="EUR")
    ↓
YFinanceFetcher.fetch_price (yfinance_fetcher.py:86)
    ↓
Normalize: _normalize_crypto_symbol("BTC", CRYPTO, "EUR")
    ↓
Returns: "BTC-EUR"
    ↓
yfinance API: yf.Ticker("BTC-EUR").info
    ↓
Parse response: price=45234.50, currency="EUR"
    ↓
Build Price object: symbol="BTC", price=45234.50, currency="EUR"
    ↓
Return to API endpoint
    ↓
JSON Response: {"symbol": "BTC", "price": 45234.50, "currency": "EUR", ...}
    ↓
User receives clean response
```

---

## Code References

- **API Endpoint:** `backend/src/api/routers/prices.py:67-141`
- **Symbol Normalization:** `backend/src/price_service/fetchers/yfinance_fetcher.py:53-84`
- **Price Fetching:** `backend/src/price_service/fetchers/yfinance_fetcher.py:86-154`
- **Historical Fetching:** `backend/src/price_service/fetchers/yfinance_fetcher.py:156-251`
- **Converter Logic:** `backend/src/price_service/converter.py:59-136`
- **Currency Validation:** `backend/src/price_service/converter.py:107-112`

---

*Last Updated: 2025-11-20*
