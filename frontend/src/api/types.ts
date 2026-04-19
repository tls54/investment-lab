// API Response Types (matching backend Pydantic models)

export type AssetType = 'stock' | 'crypto' | 'commodity' | 'forex' | 'etf';

export interface Price {
  symbol: string;
  asset_type: AssetType;
  price: number;
  timestamp: string;
  volume?: number;
  currency: string;
  source: string;
  bid?: number;
  ask?: number;
  high_24h?: number;
  low_24h?: number;
  open?: number;
  close?: number;
}

export interface PricePoint {
  timestamp: string;
  price: number;
  volume?: number;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  currency: string;
  source: string;
}

export interface HistoricalPrice {
  symbol: string;
  asset_type: AssetType;
  prices: PricePoint[];
  start_date: string;
  end_date: string;
  interval: string;
  count: number;
  message?: string; // Optional message for no data scenarios
}

// Currency conversion response (simple forex conversion)
export interface CurrencyConversionResult {
  symbol: string;
  asset_type: string;
  price: number;
  currency: string;
  native_price: number;
  native_currency: string;
  target_currency: string;
  converted_price: number;
  forex_rate: number;
  timestamp: string;
  conversion_method: 'direct' | 'forex';
  interpretation: string;
}

// Asset ratio conversion response
export interface ConversionResult {
  asset_symbol: string;
  denomination_symbol: string;
  ratio: number;
  inverse_ratio: number;
  asset_price: number;
  asset_currency: string;
  denomination_price: number;
  denomination_currency: string;
  asset_price_normalized: number;
  denomination_price_normalized: number;
  common_currency: string;
  conversion_method: 'direct' | 'triangular';
  timestamp: string;
  interpretation: string;
  inverse_interpretation: string;
}

export interface HistoricalConversionPoint {
  timestamp: string;
  date: string;
  ratio: number;
  inverse_ratio: number;
  asset_price: number;
  asset_currency: string;
  denomination_price: number;
  denomination_currency: string;
  asset_price_normalized: number;
  denomination_price_normalized: number;
  common_currency: string;
}

export interface HistoricalConversion {
  asset_symbol: string;
  denomination_symbol: string;
  start_date: string;
  end_date: string;
  interval: string;
  count: number;
  conversion_method: 'direct' | 'triangular';
  common_currency: string;
  data: HistoricalConversionPoint[];
  summary?: {
    min_ratio: number;
    max_ratio: number;
    avg_ratio: number;
  };
  message?: string; // Optional message for no data scenarios
}

export interface ForecastRequest {
  symbol: string;
  horizon_days: number;
  n_paths?: number;
  calibration_days?: number;
  asset_type?: AssetType;
  include_paths?: boolean;
  n_sample_paths?: number;
}

export interface ForecastResponse {
  symbol: string;
  current_price: number;
  horizon_days: number;
  n_paths: number;
  mean: number;
  median: number;
  std: number;
  percentiles: {
    p05: number;
    p25: number;
    p50: number;
    p75: number;
    p95: number;
  };
  var_95: number;
  cvar_95: number;
  probability_above_current: number;
  expected_return: number;
  parameters: {
    mu: number;
    sigma: number;
    S0: number;
    interpretation: {
      annual_return: string;
      annual_volatility: string;
      initial_price: string;
    };
  };
  calibration_period: {
    start: string;
    end: string;
    days: number;
  };
  sample_paths?: number[][];
}

export interface APIError {
  detail: string;
  status?: number;
}

export interface HistoricalQueryParams {
  days?: number;
  start_date?: string;
  end_date?: string;
  interval?: string;
}

export interface ForecastQueryParams {
  days?: number;
  asset_type?: AssetType;
}
