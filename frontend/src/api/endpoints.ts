import apiClient from './client';
import type {
  Price,
  HistoricalPrice,
  ConversionResult,
  HistoricalConversion,
  ForecastRequest,
  ForecastResponse,
  HistoricalQueryParams,
  ForecastQueryParams,
  AssetType,
} from './types';

// Price Endpoints

export const getCurrentPrice = async (
  symbol: string,
  assetType?: AssetType
): Promise<Price> => {
  const params: Record<string, string> = {};
  if (assetType) params.asset_type = assetType;

  const response = await apiClient.get<Price>(`/api/price/${symbol}`, { params });
  return response.data;
};

export const getHistoricalPrices = async (
  symbol: string,
  params: HistoricalQueryParams
): Promise<HistoricalPrice> => {
  const response = await apiClient.get<HistoricalPrice>(
    `/api/price/${symbol}/history`,
    { params }
  );
  return response.data;
};

// Conversion Endpoints

export const getCurrentConversion = async (
  asset: string,
  denomination: string
): Promise<ConversionResult> => {
  const response = await apiClient.get<ConversionResult>(
    `/api/convert/${asset}/${denomination}`
  );
  return response.data;
};

export const getHistoricalConversion = async (
  asset: string,
  denomination: string,
  params: HistoricalQueryParams
): Promise<HistoricalConversion> => {
  const response = await apiClient.get<HistoricalConversion>(
    `/api/convert/${asset}/${denomination}/history`,
    { params }
  );
  return response.data;
};

// Forecast Endpoints

export const getQuickForecast = async (
  symbol: string,
  params?: ForecastQueryParams
): Promise<ForecastResponse> => {
  const response = await apiClient.get<ForecastResponse>(
    `/api/forecast/gbm/${symbol}`,
    { params }
  );
  return response.data;
};

export const generateForecast = async (
  request: ForecastRequest
): Promise<ForecastResponse> => {
  const response = await apiClient.post<ForecastResponse>(
    '/api/forecast/gbm',
    request
  );
  return response.data;
};
