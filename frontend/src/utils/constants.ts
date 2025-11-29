// Denomination categories
export const CURRENCY_DENOMINATIONS = [
  { label: 'US Dollar', value: 'USD', symbol: '$', description: 'Convert to USD' },
  { label: 'British Pound', value: 'GBP', symbol: '£', description: 'Convert to GBP' },
  { label: 'Euro', value: 'EUR', symbol: '€', description: 'Convert to EUR' },
  { label: 'Japanese Yen', value: 'JPY', symbol: '¥', description: 'Convert to JPY' },
] as const;

export const ASSET_DENOMINATIONS = [
  { label: 'Bitcoin', value: 'BTC', symbol: '₿', description: 'Price in Bitcoin', isCrypto: true },
  { label: 'Ethereum', value: 'ETH', symbol: 'Ξ', description: 'Price in Ethereum', isCrypto: true },
  { label: 'Gold ETF', value: 'GLD', symbol: 'Au', description: 'Price in Gold', isCrypto: false },
  { label: 'S&P 500', value: 'SPY', symbol: 'SPY', description: 'Price in S&P 500 ETF', isCrypto: false },
] as const;

// Combined for backward compatibility
export const DENOMINATIONS = [
  { label: 'Native Currency', value: 'NATIVE', symbol: '', description: 'Show in native currency' },
  ...CURRENCY_DENOMINATIONS,
  ...ASSET_DENOMINATIONS,
] as const;

export const TIME_RANGES = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '1Y', days: 365 },
] as const;

export const PATH_COUNTS = [
  { label: '1K', value: 1000 },
  { label: '10K', value: 10000 },
  { label: '50K', value: 50000 },
  { label: '100K', value: 100000 },
] as const;

export const DEFAULT_FORECAST_CONFIG = {
  horizon_days: 30,
  n_paths: 10000,
  calibration_days: 252,
  include_paths: true,
  n_sample_paths: 100,
} as const;

export const REFRESH_INTERVALS = {
  PRICE: 60000,
  HISTORICAL: 5 * 60000,
} as const;

export const POPULAR_SYMBOLS = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'MSFT', name: 'Microsoft' },
  { symbol: 'GOOGL', name: 'Alphabet' },
  { symbol: 'AMZN', name: 'Amazon' },
  { symbol: 'NVDA', name: 'NVIDIA' },
  { symbol: 'SPY', name: 'S&P 500 ETF' },
  { symbol: 'QQQ', name: 'Nasdaq 100 ETF' },
  { symbol: 'BTC-USD', name: 'Bitcoin' },
  { symbol: 'ETH-USD', name: 'Ethereum' },
] as const;

// List of currency-agnostic crypto symbols
export const CRYPTO_SYMBOLS = ['BTC', 'ETH'] as const;

// Helper to check if a denomination is a crypto symbol (without currency suffix)
export function isCryptoDenomination(denomination: string): boolean {
  return CRYPTO_SYMBOLS.includes(denomination as any);
}

// Helper to construct full crypto symbol with asset currency
export function constructCryptoSymbol(cryptoBase: string, assetCurrency: string): string {
  return `${cryptoBase}-${assetCurrency}`;
}
