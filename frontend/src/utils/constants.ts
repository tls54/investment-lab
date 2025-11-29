export const DENOMINATIONS = [
  { label: 'Native Currency', value: 'NATIVE', symbol: '' },
  { label: 'US Dollar', value: 'USD', symbol: '$' },
  { label: 'Bitcoin', value: 'BTC-USD', symbol: '₿' },
  { label: 'Ethereum', value: 'ETH-USD', symbol: 'Ξ' },
  { label: 'Gold ETF', value: 'GLD', symbol: 'Au' },
  { label: 'British Pound', value: 'GBP', symbol: '£' },
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
