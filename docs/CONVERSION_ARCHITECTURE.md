# Conversion Architecture - Comprehensive Overview

## System Architecture

```
Frontend Request
    ↓
API Router (prices.py)
    ↓
DenominationConverter (converter.py)
    ↓
YFinanceFetcher (yfinance_fetcher.py)
    ↓
yfinance library → Yahoo Finance API
```

---

## 1. Frontend API Calls

### Current Price
```typescript
GET /api/price/{symbol}?currency=USD
```
**Returns:** Single `Price` object with current price in specified currency

### Historical Prices
```typescript
GET /api/price/{symbol}/history?days=30&currency=USD
```
**Returns:** `HistoricalPrice` object with array of price points

### Current Conversion (Ratio)
```typescript
GET /api/convert/{asset}/{denomination}?asset_currency=USD&denomination_currency=USD
```
**Returns:** `ConversionResult` with ratio and both prices

### Historical Conversion
```typescript
GET /api/convert/{asset}/{denomination}/history?days=30&asset_currency=USD&denomination_currency=USD
```
**Returns:** `HistoricalConversion` with time series of ratios

---

## 2. Backend Components

### A. API Router (`prices.py`)

**Responsibilities:**
- Route HTTP requests
- Parse query parameters
- Call converter/fetcher methods
- Handle errors and return appropriate HTTP codes

**Key Endpoints:**
1. `GET /api/price/{symbol}` - Current price
2. `GET /api/price/{symbol}/history` - Historical prices
3. `GET /api/convert/{asset}/{denomination}` - Current conversion
4. `GET /api/convert/{asset}/{denomination}/history` - Historical conversion

**Error Handling:**
- `404` - Symbol not found
- `400` - Validation error (e.g., currency mismatch)
- `429` - Rate limit exceeded
- `500` - Internal server error

### B. DenominationConverter (`converter.py`)

**Purpose:** Calculate ratios between two assets

**Core Methods:**

#### `convert(asset_symbol, denomination_symbol, asset_currency="USD", denomination_currency="USD")`
```python
# Steps:
1. Fetch asset price in asset_currency
2. Fetch denomination price in denomination_currency
3. Validate currencies match
4. Calculate ratio = asset_price / denomination_price
5. Return ConversionResult
```

**Returns:**
```python
{
    "asset_symbol": "AAPL",
    "denomination_symbol": "BTC-USD",
    "ratio": 0.00357,           # 1 AAPL = 0.00357 BTC
    "inverse_ratio": 280.11,     # 1 BTC = 280.11 AAPL
    "asset_price_usd": 242.50,
    "denomination_price_usd": 68000.00,
    "asset_currency": "USD",
    "denomination_currency": "USD",
    "timestamp": "2025-11-28T...",
    "interpretation": "1 AAPL = 0.00357 BTC-USD"
}
```

**CRITICAL VALIDATION:**
```python
if asset_price.currency != denom_price.currency:
    raise ValueError("Currency mismatch: {asset} is in {curr1} but {denom} is in {curr2}")
```

#### `convert_historical(asset_symbol, denomination_symbol, start, end, ...)`
- Same logic as `convert()` but for time series
- Fetches historical data for both assets
- Validates currency match
- Calculates ratio for each matching timestamp
- Returns array of data points

### C. YFinanceFetcher (`yfinance_fetcher.py`)

**Purpose:** Fetch price data from Yahoo Finance

**Core Methods:**

#### `fetch_price(symbol, asset_type=None, currency="USD")`

**For STOCKS/ETFs:**
```python
# Example: VUSA.L
1. Fetch from yfinance: ticker.info
2. Extract currency from yfinance data: info.get('currency')  # Returns "GBP"
3. IGNORES currency parameter for stocks (native currency always used)
4. Returns Price object with currency="GBP"
```

**For CRYPTO:**
```python
# Example: BTC with currency="EUR"
1. Normalize symbol: "BTC" → "BTC-EUR"
2. Try direct pair: "BTC-EUR"
   ✓ If exists: Returns price in EUR
   ✗ If not found: Try triangular conversion
3. Triangular conversion (if enabled):
   - Fetch BTC-USD
   - Fetch EUR-USD forex rate
   - Calculate BTC-EUR = BTC-USD × USD-EUR
4. Returns Price with currency="EUR"
```

**Triangular Conversion Logic:**
```python
def _should_try_triangular(asset_type, currency):
    # Only for CRYPTO, not for STOCKS/ETFs
    if asset_type != AssetType.CRYPTO:
        return False
    # Don't try if already USD (prevents loop)
    if currency == "USD":
        return False
    return True
```

#### `fetch_historical(symbol, start, end, interval, asset_type=None, currency="USD")`
- Same logic as `fetch_price()` but returns time series
- **RECENTLY FIXED:** Now correctly extracts currency from yfinance instead of using parameter

---

## 3. Current Behavior Matrix

| Asset | Denomination | asset_currency | denom_currency | Result | Reason |
|-------|-------------|----------------|----------------|--------|--------|
| AAPL | BTC-USD | USD (default) | USD (default) | ✅ Works | Both USD, currencies match |
| AAPL | BTC-GBP | USD | USD | ❌ 400 Error | BTC-GBP doesn't exist |
| VUSA.L | BTC-USD | USD | USD | ❌ 400 Error | VUSA.L returns GBP (native), BTC-USD returns USD → Mismatch |
| VUSA.L | BTC-GBP | USD | USD | ✅ Works | Both fetch in GBP (crypto triangular works) |
| VUSA.L | USD | N/A | N/A | ❌ Not possible | No conversion endpoint for currency conversion |
| VUSA.L | GBP | USD | USD | ❌ 400 Error | "GBP" is not a valid yfinance symbol |

---

## 4. What's Missing / Problems

### Problem 1: Cross-Currency Conversions
**Issue:** Cannot convert VUSA.L (GBP) to BTC-USD (USD)

**Why:**
- `converter.py` line 107-112: Strict currency match validation
- No triangular conversion at converter level

**What's needed:**
```
VUSA.L (GBP) + BTC-USD (USD) should:
1. Fetch VUSA.L → £98 (GBP)
2. Fetch BTC-USD → $68,000 (USD)
3. Fetch GBP-USD forex → 1.27
4. Convert: VUSA.L in USD = £98 × 1.27 = $124.46
5. Calculate ratio: $124.46 / $68,000 = 0.00183 BTC
```

### Problem 2: Simple Currency Conversion
**Issue:** Cannot convert VUSA.L to USD (no ratio, just currency conversion)

**Frontend wants:**
```
GET /api/price/VUSA.L/convert-currency?to=USD
→ Returns VUSA.L price in USD ($124.46)
```

**Currently:** No such endpoint exists

### Problem 3: Denomination Symbols
**Issue:** "GBP", "USD" are not valid yfinance symbols

**Frontend sends:**
- `denomination="USD"` → Not a yfinance symbol
- `denomination="GBP"` → Not a yfinance symbol

**Should send:**
- For currency conversion: Different endpoint
- For asset pricing: Actual asset symbols (BTC-USD, GLD, etc.)

### Problem 4: Inconsistent Naming
**Issue:** Fields named `asset_price_usd` / `denomination_price_usd` even when not in USD

**Current code:**
```python
"asset_price_usd": asset_price.price,  # Misleading - could be GBP!
"denomination_price_usd": denom_price.price
```

**Should be:**
```python
"asset_price": asset_price.price,
"asset_currency": asset_price.currency,
"denomination_price": denom_price.price,
"denomination_currency": denom_price.currency
```

---

## 5. What Works (Triangular Conversion in Fetcher)

**Good news:** `yfinance_fetcher.py` DOES have triangular conversion for CRYPTO!

**Example that works:**
```python
# Fetch BTC in GBP
fetch_price("BTC", asset_type=CRYPTO, currency="GBP")

# Process:
1. Try direct: "BTC-GBP"
   → If exists: ✓ Use it
   → If not: Continue to step 2
2. Triangular conversion:
   - Fetch BTC-USD → $68,000
   - Fetch GBP-USD forex → 0.787
   - Calculate: BTC-GBP = $68,000 × 0.787 = £53,516
3. Return Price(currency="GBP", price=53516)
```

**Limitation:** Only works for CRYPTO, not for STOCKS/ETFs

---

## 6. Solution Architecture

### Option A: Implement Triangular Conversion in Converter
**Location:** `converter.py` - Update `convert()` and `convert_historical()`

**Logic:**
```python
async def convert(asset_symbol, denomination_symbol, ...):
    # Fetch both
    asset_price = await fetch_price(asset_symbol, currency=asset_currency)
    denom_price = await fetch_price(denomination_symbol, currency=denomination_currency)

    # Check currencies
    if asset_price.currency != denom_price.currency:
        # NEW: Instead of raising error, convert via USD
        if asset_price.currency != "USD":
            # Convert asset to USD
            forex_rate = await fetch_forex_rate(asset_price.currency, "USD")
            asset_price_usd = asset_price.price * forex_rate
        else:
            asset_price_usd = asset_price.price

        if denom_price.currency != "USD":
            # Convert denom to USD
            forex_rate = await fetch_forex_rate(denom_price.currency, "USD")
            denom_price_usd = denom_price.price * forex_rate
        else:
            denom_price_usd = denom_price.price

        # Calculate ratio in USD terms
        ratio = asset_price_usd / denom_price_usd
    else:
        # Direct calculation (same currency)
        ratio = asset_price.price / denom_price.price

    return ConversionResult(...)
```

### Option B: Add Currency Conversion Endpoint
**New endpoint:** `GET /api/price/{symbol}/in/{currency}`

**Example:**
```
GET /api/price/VUSA.L/in/USD
→ Returns: { "symbol": "VUSA.L", "price": 124.46, "currency": "USD", "native_price": 98.00, "native_currency": "GBP", "forex_rate": 1.27 }
```

### Option C: Smart Converter with Auto-Detection
**Hybrid approach:**
1. Try direct conversion (same currency)
2. If currency mismatch → Auto-apply triangular conversion
3. Log/mark result as "triangular" in metadata

---

## 7. Recommended Implementation

### Phase 1: Fix Currency Mismatch (Immediate)
**Goal:** Make VUSA.L + BTC-USD work

**Changes:**
1. Add `_convert_via_usd()` method to `converter.py`
2. Add forex rate fetching (reuse from `yfinance_fetcher.py`)
3. Update `convert()` to call triangular conversion on currency mismatch
4. Update `convert_historical()` similarly

### Phase 2: Clean Up API (Short-term)
**Goal:** Better naming and structure

**Changes:**
1. Rename `asset_price_usd` → `asset_price`
2. Add `conversion_method` field: "direct" | "triangular"
3. Better error messages

### Phase 3: Currency Conversion Endpoint (Optional)
**Goal:** Support simple "VUSA.L in USD" without ratio

**Changes:**
1. Add new endpoint for currency conversion only
2. Frontend can choose: ratio mode vs currency conversion mode

---

## 8. Frontend Integration Points

### Current Frontend Calls:
```typescript
// Native mode (denomination = "NATIVE")
→ No conversion, just show price.currency

// Conversion mode (denomination = "BTC-USD", "GLD", etc.)
→ GET /api/convert/{symbol}/{denomination}
→ Shows ratio

// Problem: denomination = "USD" for VUSA.L
→ Currently tries: GET /api/convert/VUSA.L/USD
→ "USD" is not a valid yfinance symbol
→ Backend error
```

### Proposed Frontend Logic:
```typescript
if (denomination === "NATIVE") {
    // Show native price
    use priceQuery.data
} else if (isCurrencyCode(denomination)) {  // "USD", "GBP", "EUR"
    // Use currency conversion endpoint (Phase 3)
    GET /api/price/{symbol}/in/{denomination}
} else {
    // Use ratio conversion (current logic)
    GET /api/convert/{symbol}/{denomination}
}
```

---

## Summary

**Current State (Updated 2025-11-29):**
- ✅ Currency conversion implemented (Level 1)
  - Simple forex conversion for AAPL in GBP, VUSA.L in USD
  - Supports USD, GBP, EUR, JPY
  - Both current and historical
- ✅ Cross-currency ratio conversion implemented (Level 2)
  - Triangular conversion in `converter.py` via USD
  - Works for all asset types
  - Both current and historical
- ✅ Smart crypto matching implemented
  - Frontend auto-constructs BTC-GBP for GBP assets, BTC-USD for USD assets
  - Avoids unnecessary cross-currency conversion
  - User selects "Bitcoin", system picks right pair
- ✅ Crypto triangular conversion for current prices
  - `yfinance_fetcher.py` supports BTC-MXN via BTC-USD × USD-MXN
  - Works for rare currencies

**Known Limitation (Future Enhancement):**
- ⚠️ **Crypto Historical Triangular for Rare Currencies**
  - `fetch_historical()` in `yfinance_fetcher.py` lacks triangular fallback
  - Current price works: BTC-MXN via triangular ✅
  - Historical fails: BTC-MXN history returns 404 if pair doesn't exist ❌
  - **Impact:** Only affects rare currencies (MXN, ZAR, THB, etc.)
  - **Common currencies work fine:** USD, GBP, EUR have direct pairs
  - **To fix:** Add triangular logic to `fetch_historical()` similar to `fetch_price()`
    - Try direct pair first (BTC-MXN)
    - If not found, fetch BTC-USD history and USD-MXN forex rate
    - Apply forex conversion to each historical point
    - Note: Uses current forex rate for all historical points (less accurate)

**All Main Features Complete:**
- VUSA.L / BTC-USD works via smart matching (uses BTC-GBP) ✅
- AAPL in GBP works via currency conversion ✅
- Cross-currency asset ratios work via triangular ✅
