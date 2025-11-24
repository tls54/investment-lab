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
}

export interface HistoricalPrice {
  symbol: string;
  asset_type: AssetType;
  prices: PricePoint[];
  start_date: string;
  end_date: string;
  interval: string;
  count: number;
}

export interface ConversionResult {
  asset_symbol: string;
  denomination_symbol: string;
  ratio: number;
  inverse_ratio: number;
  asset_price_usd: number;
  denomination_price_usd: number;
  asset_currency: string;
  denomination_currency: string;
  timestamp: string;
  interpretation: string;
  inverse_interpretation: string;
}

export interface HistoricalConversionPoint {
  timestamp: string;
  date: string;
  ratio: number;
  inverse_ratio: number;
  asset_price_usd: number;
  denomination_price_usd: number;
}

export interface HistoricalConversion {
  asset_symbol: string;
  denomination_symbol: string;
  start_date: string;
  end_date: string;
  interval: string;
  count: number;
  data: HistoricalConversionPoint[];
  summary: {
    min_ratio: number;
    max_ratio: number;
    avg_ratio: number;
  };
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
