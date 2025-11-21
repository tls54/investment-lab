# Cryptocurrency Multi-Currency Support

## Overview

Investment Lab supports pricing cryptocurrencies in multiple fiat currencies beyond USD. This allows global users to view crypto prices in their local currency without manual conversion.

## Supported Currencies

The following currencies are **confirmed to work** with yfinance:

| Code | Currency | Region | Example |
|------|----------|--------|---------|
| USD | US Dollar | United States | BTC-USD |
| EUR | Euro | European Union | BTC-EUR |
| GBP | British Pound | United Kingdom | BTC-GBP |
| JPY | Japanese Yen | Japan | BTC-JPY |
| AUD | Australian Dollar | Australia | BTC-AUD |
| CAD | Canadian Dollar | Canada | BTC-CAD |

**Note:** Additional currencies may work depending on yfinance data availability. The system will return an error if a currency pair is not available.

## API Usage

### Current Price

**Endpoint:** `GET /api/price/{symbol}`

**Parameters:**
- `symbol`: Crypto symbol (e.g., BTC, ETH)
- `asset_type`: Set to `crypto`
- `currency`: Fiat currency code (default: USD)

**Examples:**

```bash
# Bitcoin in USD (default)
GET /api/price/BTC?asset_type=crypto

# Bitcoin in Euro
GET /api/price/BTC?asset_type=crypto&currency=EUR

# Ethereum in British Pounds
GET /api/price/ETH?asset_type=crypto&currency=GBP

# Bitcoin in Japanese Yen
GET /api/price/BTC?asset_type=crypto&currency=JPY
```

**Response:**
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

### Historical Prices

**Endpoint:** `GET /api/price/{symbol}/history`

**Parameters:**
- `symbol`: Crypto symbol
- `asset_type`: Set to `crypto`
- `currency`: Fiat currency code (default: USD)
- `days`: Number of days (or use `start_date`/`end_date`)

**Examples:**

```bash
# Bitcoin in EUR for last 7 days
GET /api/price/BTC/history?asset_type=crypto&currency=EUR&days=7

# Ethereum in GBP with custom date range
GET /api/price/ETH/history?asset_type=crypto&currency=GBP&start_date=2025-01-01&end_date=2025-11-20
```

**Response:**
```json
{
  "symbol": "BTC",
  "asset_type": "crypto",
  "start_date": "2025-11-13",
  "end_date": "2025-11-20",
  "interval": "1d",
  "count": 7,
  "prices": [
    {
      "timestamp": "2025-11-13T00:00:00",
      "price": 44500.00,
      "currency": "EUR",
      "volume": 1234567.0
    },
    ...
  ]
}
```

### Denomination Conversion with Currency

**Endpoint:** `GET /api/convert/{asset}/{denomination}`

**Examples:**

```bash
# How many BTC is one AAPL share? (Both in USD)
GET /api/convert/AAPL/BTC

# How many BTC (in EUR) is one AAPL share?
GET /api/convert/AAPL/BTC?denomination_type=crypto&denomination_currency=EUR

# How many ETH (in GBP) is one MSFT share?
GET /api/convert/MSFT/ETH?denomination_type=crypto&denomination_currency=GBP
```

**Important:** For accurate conversions, both assets should be priced in the same currency. Cross-currency conversion is validated and will return an error if currencies don't match.

## Implementation Details

### How It Works

1. **Symbol Normalization**: When `asset_type=crypto` and a currency is specified, the system automatically creates the yfinance symbol:
   - Input: `BTC` + `EUR` → yfinance symbol: `BTC-EUR`
   - Input: `ETH` + `GBP` → yfinance symbol: `ETH-GBP`

2. **Known Crypto Symbols**: The system maintains a list of common crypto symbols and automatically applies currency suffixes:
   ```python
   CRYPTO_SYMBOLS = {
       "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP",
       "DOGE", "ADA", "TRX", "AVAX", "LINK", "DOT", "MATIC",
       "UNI", "LTC", "BCH", "XLM", "ATOM", "ETC"
   }
   ```

3. **Already Suffixed**: If the symbol already has a suffix (e.g., `BTC-EUR`), it's used as-is.

### Error Handling

**Unsupported Currency:**
```bash
GET /api/price/BTC?asset_type=crypto&currency=INVALID
```

**Response:** `404 Not Found`
```json
{
  "detail": "Symbol 'BTC' not found"
}
```

**Currency Mismatch in Conversion:**
```bash
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=EUR
```

**Response:** `500 Internal Server Error`
```json
{
  "detail": "Currency mismatch: AAPL is priced in USD but BTC is priced in EUR. Cross-currency conversion is not yet supported."
}
```

## Testing

Run the currency test suite:

```bash
cd backend

# Run all currency tests
pytest tests/test_crypto_currencies.py -v

# Run only supported currency tests
pytest tests/test_crypto_currencies.py::TestCryptoCurrentPrice::test_supported_currencies -v

# Test a specific currency
pytest tests/test_crypto_currencies.py::TestCryptoCurrentPrice::test_supported_currencies[EUR] -v

# See which currencies are documented as working
pytest tests/test_crypto_currencies.py::TestCurrencyValidation::test_common_supported_currencies -v -s
```

## Limitations

### 1. Currency Availability Depends on yfinance
Not all crypto-fiat pairs are available. Common pairs (USD, EUR, GBP, JPY) work reliably, but exotic currencies may not have data.

### 2. No Triangular Conversion (Yet)
If `BTC-INR` is not available directly, the system **cannot** calculate it via:
```
BTC-INR = BTC-USD × USD-INR
```

This feature is planned for a future release. See: `tests/test_crypto_currencies.py::TestTriangularConversion` (currently marked as `skip`).

### 3. Cross-Currency Conversion Not Supported
When using `/api/convert/{asset}/{denomination}`, both assets must be in the same currency:

**Works:**
```bash
# Both in USD
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=USD
```

**Doesn't Work:**
```bash
# Different currencies
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=EUR
# Returns error: "Cross-currency conversion is not yet supported"
```

## Future Enhancements

### Triangular Conversion
**Status:** Planned

Automatically calculate missing pairs via USD:
```python
# If BTC-INR not available
btc_usd = fetch_price("BTC", currency="USD")
usd_inr = fetch_forex_rate("USD", "INR")
btc_inr = btc_usd * usd_inr
```

**Implementation:**
1. Add forex rate fetcher (Alpha Vantage supports this)
2. Implement fallback logic in `yfinance_fetcher.py`
3. Enable tests in `test_crypto_currencies.py::TestTriangularConversion`

### Cross-Currency Denomination Conversion
**Status:** Planned

Allow conversions like:
```bash
# AAPL (in USD) priced in BTC (in EUR)
GET /api/convert/AAPL/BTC?asset_currency=USD&denomination_currency=EUR
```

Would calculate:
```
AAPL_USD / BTC_EUR
```

### Real-Time Exchange Rates
**Status:** Future

Cache forex rates and update periodically for better performance.

## Code References

- **Fetcher Implementation:** `backend/src/price_service/fetchers/yfinance_fetcher.py:53`
- **Symbol Normalization:** `backend/src/price_service/fetchers/yfinance_fetcher.py:53-84`
- **API Endpoints:** `backend/src/api/routers/prices.py:68-141`
- **Test Suite:** `backend/tests/test_crypto_currencies.py`

## Examples in Practice

### Portfolio Tracker (European User)

```bash
# Fetch all holdings in EUR
GET /api/price/BTC?asset_type=crypto&currency=EUR
GET /api/price/ETH?asset_type=crypto&currency=EUR
GET /api/price/SOL?asset_type=crypto&currency=EUR

# Calculate total portfolio value
total = (btc_amount * btc_eur) + (eth_amount * eth_eur) + (sol_amount * sol_eur)
```

### Historical Analysis (Japanese User)

```bash
# Compare BTC vs ETH performance in JPY over 30 days
GET /api/price/BTC/history?asset_type=crypto&currency=JPY&days=30
GET /api/price/ETH/history?asset_type=crypto&currency=JPY&days=30

# Plot both on same chart in JPY
```

### Cross-Asset Comparison (UK User)

```bash
# How has AAPL/BTC ratio changed? (Both in GBP for consistency)
GET /api/convert/AAPL/BTC/history?denomination_type=crypto&denomination_currency=GBP&days=90
```

---

*Last Updated: 2025-11-20*
