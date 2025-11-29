import { Card } from '../common';
import { formatPrice } from '../../utils';
import type { ForecastResponse } from '../../api/types';

interface ConfidenceIntervalsProps {
  data: ForecastResponse;
  currency?: string;
}

export function ConfidenceIntervals({ data, currency = 'USD' }: ConfidenceIntervalsProps) {
  const { p05, p25, p50, p75, p95 } = data.percentiles;
  const current = data.current_price;

  // Calculate positions as percentages
  const min = p05 * 0.95;
  const max = p95 * 1.05;
  const range = max - min;

  const getPosition = (value: number) => ((value - min) / range) * 100;

  const percentileMarkers = [
    { label: 'P5', value: p05, color: 'bg-red-500', textColor: 'text-red-400' },
    { label: 'P25', value: p25, color: 'bg-orange-500', textColor: 'text-orange-400' },
    { label: 'P50', value: p50, color: 'bg-yellow-500', textColor: 'text-yellow-400' },
    { label: 'P75', value: p75, color: 'bg-emerald-500', textColor: 'text-emerald-400' },
    { label: 'P95', value: p95, color: 'bg-green-500', textColor: 'text-green-400' },
  ];

  return (
    <Card title="Confidence Intervals" subtitle="Price range probabilities">
      <div className="space-y-8">
        {/* Visual Bar */}
        <div className="relative pt-10 pb-8">
          {/* Background bar with gradient */}
          <div className="h-3 bg-gradient-to-r from-red-500/30 via-yellow-500/30 to-green-500/30 rounded-full" />

          {/* Percentile markers */}
          {percentileMarkers.map((marker) => (
            <div
              key={marker.label}
              className="absolute"
              style={{ left: `${getPosition(marker.value)}%`, top: '0' }}
            >
              <div className="relative">
                <div
                  className={`w-3 h-3 ${marker.color} rounded-full transform -translate-x-1/2 shadow-lg`}
                  style={{ marginTop: '32px' }}
                />
                <div className={`absolute bottom-full mb-1 transform -translate-x-1/2 text-xs ${marker.textColor} font-medium whitespace-nowrap`}>
                  {marker.label}
                </div>
                <div className="absolute top-full mt-3 transform -translate-x-1/2 text-xs text-text-primary font-mono whitespace-nowrap">
                  {formatPrice(marker.value, currency)}
                </div>
              </div>
            </div>
          ))}

          {/* Current price marker */}
          <div
            className="absolute"
            style={{ left: `${getPosition(current)}%`, top: '0' }}
          >
            <div className="relative">
              <div
                className="w-4 h-4 bg-accent-blue transform -translate-x-1/2 rotate-45 shadow-glow"
                style={{ marginTop: '30px' }}
              />
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-accent-blue rotate-45" />
            <span className="text-text-secondary">Current: {formatPrice(current, currency)}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-2 bg-gradient-to-r from-red-500/50 via-yellow-500/50 to-green-500/50 rounded-full" />
            <span className="text-text-secondary">Probability distribution</span>
          </div>
        </div>

        {/* Interval Table */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-dark-700 rounded-lg border border-dark-600">
            <div className="text-xs text-text-muted uppercase tracking-wide mb-2">90% Range</div>
            <div className="text-sm font-medium text-text-primary font-mono">
              {formatPrice(p05, currency)}
            </div>
            <div className="text-xs text-text-muted my-1">to</div>
            <div className="text-sm font-medium text-text-primary font-mono">
              {formatPrice(p95, currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-dark-700 rounded-lg border border-dark-600">
            <div className="text-xs text-text-muted uppercase tracking-wide mb-2">50% Range</div>
            <div className="text-sm font-medium text-text-primary font-mono">
              {formatPrice(p25, currency)}
            </div>
            <div className="text-xs text-text-muted my-1">to</div>
            <div className="text-sm font-medium text-text-primary font-mono">
              {formatPrice(p75, currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-dark-700 rounded-lg border border-dark-600">
            <div className="text-xs text-text-muted uppercase tracking-wide mb-2">Median (P50)</div>
            <div className="text-lg font-bold text-accent-purple font-mono mt-2">
              {formatPrice(p50, currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-dark-700 rounded-lg border border-dark-600">
            <div className="text-xs text-text-muted uppercase tracking-wide mb-2">Mean</div>
            <div className="text-lg font-bold text-accent-blue font-mono mt-2">
              {formatPrice(data.mean, currency)}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
