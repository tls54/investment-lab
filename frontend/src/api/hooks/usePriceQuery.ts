import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { getCurrentPrice, getHistoricalPrices } from '../endpoints';
import type { Price, HistoricalPrice, HistoricalQueryParams, AssetType } from '../types';

export const usePriceQuery = (
  symbol: string | undefined,
  options?: {
    refetchInterval?: number;
    enabled?: boolean;
    assetType?: AssetType;
  }
): UseQueryResult<Price, Error> => {
  return useQuery({
    queryKey: ['price', symbol, options?.assetType],
    queryFn: () => getCurrentPrice(symbol!, options?.assetType),
    enabled: !!symbol && (options?.enabled ?? true),
    staleTime: 60000,
    refetchInterval: options?.refetchInterval,
    retry: 2,
  });
};

export const useHistoricalQuery = (
  symbol: string | undefined,
  params: HistoricalQueryParams,
  enabled: boolean = true
): UseQueryResult<HistoricalPrice, Error> => {
  return useQuery({
    queryKey: ['historical', symbol, params],
    queryFn: () => getHistoricalPrices(symbol!, params),
    enabled: !!symbol && enabled,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
};
