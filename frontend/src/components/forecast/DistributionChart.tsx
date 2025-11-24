import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card } from '../common';
import { formatPrice } from '../../utils';
import type { ForecastResponse } from '../../api/types';

interface DistributionChartProps {
  data: ForecastResponse;
  height?: number;
}

export function DistributionChart({ data, height = 300 }: DistributionChartProps) {
  // Create histogram bins from percentiles or sample paths
  const createHistogramData = () => {
    const { p05, p25, p50, p75, p95 } = data.percentiles;
    const min = p05 * 0.95;
    const max = p95 * 1.05;
    const binCount = 20;
    const binWidth = (max - min) / binCount;

    // If we have sample paths, use them for accurate histogram
    if (data.sample_paths && data.sample_paths.length > 0) {
      const terminalPrices = data.sample_paths.map(
        (path) => path[path.length - 1]
      );
      const bins = Array(binCount).fill(0);

      terminalPrices.forEach((price) => {
        const binIndex = Math.min(
          Math.floor((price - min) / binWidth),
          binCount - 1
        );
        if (binIndex >= 0) bins[binIndex]++;
      });

      return bins.map((count, i) => ({
        price: min + (i + 0.5) * binWidth,
        count,
        range: `${formatPrice(min + i * binWidth, 'USD')} - ${formatPrice(min + (i + 1) * binWidth, 'USD')}`,
      }));
    }

    // Approximate from percentiles using normal distribution
    // Silence unused variable warnings - these could be used for more sophisticated approximation
    void p25;
    void p50;
    void p75;

    const bins = [];
    for (let i = 0; i < binCount; i++) {
      const price = min + (i + 0.5) * binWidth;
      // Simplified approximation
      const distFromMedian = Math.abs(price - data.median);
      const normalizedDist = distFromMedian / data.std;
      const count = Math.max(0, Math.exp(-0.5 * normalizedDist * normalizedDist) * 100);
      bins.push({
        price,
        count: Math.round(count),
        range: `${formatPrice(min + i * binWidth, 'USD')} - ${formatPrice(min + (i + 1) * binWidth, 'USD')}`,
      });
    }

    return bins;
  };

  const histogramData = createHistogramData();

  if (!data.sample_paths || data.sample_paths.length === 0) {
    return (
      <Card title="Price Distribution" subtitle="Enable sample paths to see distribution">
        <div className="h-[300px] flex items-center justify-center">
          <div className="text-center text-text-muted">
            <p className="mb-2">Distribution chart requires sample paths</p>
            <p className="text-sm">Enable "Include sample paths" in advanced options</p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card title="Price Distribution" subtitle={`${data.horizon_days}-day forecast distribution`}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.9} />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.4} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" vertical={false} />
          <XAxis
            dataKey="price"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickFormatter={(value) => formatPrice(value, 'USD')}
            stroke="#2a2a3a"
          />
          <YAxis
            tick={{ fontSize: 11, fill: '#64748b' }}
            stroke="#2a2a3a"
            label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a24',
              border: '1px solid #2a2a3a',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            }}
            labelStyle={{ color: '#f1f5f9' }}
            itemStyle={{ color: '#94a3b8' }}
            formatter={(value: number) => [value, 'Count']}
            labelFormatter={(_, payload) => payload[0]?.payload?.range || ''}
          />
          <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
          <ReferenceLine
            x={data.current_price}
            stroke="#ef4444"
            strokeDasharray="5 5"
            strokeWidth={2}
            label={{ value: 'Current', fill: '#ef4444', position: 'top', fontSize: 11 }}
          />
          <ReferenceLine
            x={data.mean}
            stroke="#10b981"
            strokeDasharray="5 5"
            strokeWidth={2}
            label={{ value: 'Expected', fill: '#10b981', position: 'top', fontSize: 11 }}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
