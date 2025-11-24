import { TrendingUp, TrendingDown, BarChart3, Cpu } from 'lucide-react';
import { Card } from '../common';
import { formatPrice } from '../../utils';
import type { ForecastResponse } from '../../api/types';

interface ForecastSummaryProps {
  data: ForecastResponse;
}

export function ForecastSummary({ data }: ForecastSummaryProps) {
  const expectedReturn = data.expected_return * 100;
  const isPositive = expectedReturn >= 0;

  return (
    <Card>
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        {/* Symbol and Price Info */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-text-primary">{data.symbol}</h2>
            <span className="px-3 py-1 bg-accent-purple/10 text-accent-purple text-sm font-medium rounded-lg">
              {data.horizon_days}-Day Forecast
            </span>
          </div>
          <div className="flex items-center gap-6">
            <div>
              <span className="text-sm text-text-muted block mb-1">Current Price</span>
              <div className="text-2xl font-bold text-text-primary font-mono">
                {formatPrice(data.current_price, 'USD')}
              </div>
            </div>
            <div className="text-text-muted text-2xl">→</div>
            <div>
              <span className="text-sm text-text-muted block mb-1">Expected Price</span>
              <div className="text-2xl font-bold text-accent-blue font-mono">
                {formatPrice(data.mean, 'USD')}
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="flex items-center gap-8">
          <div className={`text-center ${isPositive ? 'text-gain' : 'text-loss'}`}>
            {isPositive ? (
              <TrendingUp className="w-10 h-10 mx-auto mb-2" />
            ) : (
              <TrendingDown className="w-10 h-10 mx-auto mb-2" />
            )}
            <div className="text-2xl font-bold font-mono">
              {isPositive ? '+' : ''}{expectedReturn.toFixed(2)}%
            </div>
            <div className="text-sm text-text-muted">Expected Return</div>
          </div>

          <div className="text-center">
            <BarChart3 className="w-10 h-10 mx-auto mb-2 text-accent-purple" />
            <div className="text-2xl font-bold text-text-primary font-mono">
              {(data.probability_above_current * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-text-muted">Prob. of Gain</div>
          </div>
        </div>
      </div>

      {/* Model Parameters */}
      <div className="mt-6 pt-6 border-t border-dark-600">
        <div className="flex items-center gap-2 text-sm text-text-muted mb-3">
          <Cpu className="w-4 h-4" />
          Model Parameters (Geometric Brownian Motion)
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="p-3 bg-dark-700 rounded-lg">
            <span className="text-text-muted block mb-1">Annual Return</span>
            <span className="font-medium text-text-primary">{data.parameters.interpretation.annual_return}</span>
          </div>
          <div className="p-3 bg-dark-700 rounded-lg">
            <span className="text-text-muted block mb-1">Annual Volatility</span>
            <span className="font-medium text-text-primary">{data.parameters.interpretation.annual_volatility}</span>
          </div>
          <div className="p-3 bg-dark-700 rounded-lg">
            <span className="text-text-muted block mb-1">Simulations</span>
            <span className="font-medium text-accent-cyan">{data.n_paths.toLocaleString()}</span>
          </div>
          <div className="p-3 bg-dark-700 rounded-lg">
            <span className="text-text-muted block mb-1">Horizon</span>
            <span className="font-medium text-text-primary">{data.horizon_days} days</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
