import { useMutation, type UseMutationResult } from '@tanstack/react-query';
import { generateForecast } from '../endpoints';
import type { ForecastRequest, ForecastResponse } from '../types';

export const useForecastMutation = (): UseMutationResult<
  ForecastResponse,
  Error,
  ForecastRequest
> => {
  return useMutation({
    mutationFn: generateForecast,
    retry: 1,
  });
};
