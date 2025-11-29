import { AlertTriangle, TrendingUp, Percent, DollarSign } from 'lucide-react';
import { Card } from '../common';
import { formatPrice } from '../../utils';
import type { ForecastResponse } from '../../api/types';

interface RiskMetricsProps {
  data: ForecastResponse;
  currency?: string;
}

export function RiskMetrics({ data, currency = 'USD' }: RiskMetricsProps) {
  const metrics = [
    {
      icon: AlertTriangle,
      label: 'Value at Risk (95%)',
      value: formatPrice(data.var_95, currency),
      description: '5% chance of losing more than this amount',
      iconColor: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/20',
    },
    {
      icon: DollarSign,
      label: 'Conditional VaR (95%)',
      value: formatPrice(data.cvar_95, currency),
      description: 'Average loss in the worst 5% of scenarios',
      iconColor: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/20',
    },
    {
      icon: TrendingUp,
      label: 'Probability of Gain',
      value: `${(data.probability_above_current * 100).toFixed(1)}%`,
      description: 'Chance that price will be higher',
      iconColor: data.probability_above_current >= 0.5 ? 'text-gain' : 'text-loss',
      bgColor: data.probability_above_current >= 0.5 ? 'bg-gain/10' : 'bg-loss/10',
      borderColor: data.probability_above_current >= 0.5 ? 'border-gain/20' : 'border-loss/20',
    },
    {
      icon: Percent,
      label: 'Expected Return',
      value: `${data.expected_return >= 0 ? '+' : ''}${(data.expected_return * 100).toFixed(2)}%`,
      description: `Over ${data.horizon_days} days`,
      iconColor: data.expected_return >= 0 ? 'text-gain' : 'text-loss',
      bgColor: data.expected_return >= 0 ? 'bg-gain/10' : 'bg-loss/10',
      borderColor: data.expected_return >= 0 ? 'border-gain/20' : 'border-loss/20',
    },
  ];

  return (
    <Card title="Risk Metrics" subtitle="Key risk indicators">
      <div className="grid md:grid-cols-2 gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className={`flex items-start gap-4 p-4 ${metric.bgColor} rounded-lg border ${metric.borderColor}`}
          >
            <div className={`p-2.5 rounded-lg bg-dark-800 ${metric.iconColor}`}>
              <metric.icon className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-text-secondary mb-1">{metric.label}</div>
              <div className="text-xl font-bold text-text-primary font-mono">{metric.value}</div>
              <div className="text-xs text-text-muted mt-1">{metric.description}</div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
