import { useSearchParams } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import {
  ForecastForm,
  ForecastSummary,
  ConfidenceIntervals,
  DistributionChart,
  RiskMetrics,
} from '../components/forecast';
import { ErrorMessage } from '../components/common';
import { useForecastMutation } from '../api/hooks';
import { getCurrencyFromSymbol } from '../utils/formatters';
import type { ForecastRequest } from '../api/types';

export default function ForecastPage() {
  const [searchParams] = useSearchParams();
  const initialSymbol = searchParams.get('symbol') || '';

  const forecastMutation = useForecastMutation();

  // Extract currency from the symbol
  const currency = forecastMutation.data?.symbol
    ? getCurrencyFromSymbol(forecastMutation.data.symbol)
    : 'USD';

  const handleSubmit = (config: ForecastRequest) => {
    forecastMutation.mutate(config);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Price Forecast</h1>
        <p className="text-text-muted mt-1">
          Generate probabilistic price forecasts using Monte Carlo simulation with Geometric Brownian Motion
        </p>
      </div>

      {/* Forecast Form */}
      <ForecastForm
        onSubmit={handleSubmit}
        loading={forecastMutation.isPending}
        initialSymbol={initialSymbol}
      />

      {/* Error State */}
      {forecastMutation.isError && (
        <ErrorMessage
          error={forecastMutation.error}
          title="Forecast Failed"
          onRetry={() => forecastMutation.reset()}
        />
      )}

      {/* Results */}
      {forecastMutation.isSuccess && forecastMutation.data && (
        <div className="space-y-6">
          <ForecastSummary data={forecastMutation.data} currency={currency} />
          <ConfidenceIntervals data={forecastMutation.data} currency={currency} />
          <div className="grid lg:grid-cols-2 gap-6">
            <DistributionChart data={forecastMutation.data} currency={currency} />
            <RiskMetrics data={forecastMutation.data} currency={currency} />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!forecastMutation.isPending && !forecastMutation.isSuccess && !forecastMutation.isError && (
        <div className="text-center py-16">
          <TrendingUp className="w-16 h-16 mx-auto text-text-muted mb-4" />
          <p className="text-text-secondary text-lg mb-2">Ready to forecast</p>
          <p className="text-text-muted">
            Configure the parameters above and click "Generate Forecast" to see probabilistic price predictions
          </p>
        </div>
      )}
    </div>
  );
}
