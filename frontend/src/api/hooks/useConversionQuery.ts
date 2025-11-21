import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { getCurrentConversion, getHistoricalConversion } from '../endpoints';
import type { ConversionResult, HistoricalConversion, HistoricalQueryParams } from '../types';

export const useConversionQuery = (
  asset: string | undefined,
  denomination: string | undefined,
  enabled: boolean = true
): UseQueryResult<ConversionResult, Error> => {
  return useQuery({
    queryKey: ['conversion', asset, denomination],
    queryFn: () => getCurrentConversion(asset!, denomination!),
    enabled: !!asset && !!denomination && enabled,
    staleTime: 60000,
    retry: 2,
  });
};

export const useHistoricalConversionQuery = (
  asset: string | undefined,
  denomination: string | undefined,
  params: HistoricalQueryParams,
  enabled: boolean = true
): UseQueryResult<HistoricalConversion, Error> => {
  return useQuery({
    queryKey: ['historical-conversion', asset, denomination, params],
    queryFn: () => getHistoricalConversion(asset!, denomination!, params),
    enabled: !!asset && !!denomination && enabled,
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });
};
