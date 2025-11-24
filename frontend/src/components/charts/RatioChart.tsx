import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, LoadingSpinner, ErrorMessage } from '../common';
import { formatTimestamp, formatRatio } from '../../utils';
import type { HistoricalConversion } from '../../api/types';

interface RatioChartProps {
  data?: HistoricalConversion;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  height?: number;
}

export function RatioChart({
  data,
  loading,
  error,
  onRetry,
  height = 400,
}: RatioChartProps) {
  if (loading) {
    return (
      <Card title="Ratio History">
        <LoadingSpinner message="Loading chart data..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Ratio History">
        <ErrorMessage error={error} onRetry={onRetry} />
      </Card>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <Card title="Ratio History">
        <div className="text-center py-12 text-text-muted">
          No historical data available
        </div>
      </Card>
    );
  }

  const chartData = data.data.map((point) => ({
    timestamp: point.timestamp,
    ratio: point.ratio,
    date: formatTimestamp(point.timestamp, 'date'),
  }));

  const ratios = chartData.map((d) => d.ratio);
  const minRatio = Math.min(...ratios);
  const maxRatio = Math.max(...ratios);
  const padding = (maxRatio - minRatio) * 0.1;

  const isPositive = chartData[chartData.length - 1].ratio >= chartData[0].ratio;
  const gradientColor = isPositive ? '#10b981' : '#ef4444';
  const strokeColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <Card
      title={`${data.asset_symbol} / ${data.denomination_symbol}`}
      subtitle={`${data.count} data points`}
    >
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="ratioGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={gradientColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={gradientColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a38" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={{ stroke: '#2a2a38' }}
          />
          <YAxis
            domain={[minRatio - padding, maxRatio + padding]}
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatRatio(value)}
            width={80}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a24',
              border: '1px solid #2a2a38',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
            }}
            labelStyle={{ color: '#f1f5f9' }}
            itemStyle={{ color: '#94a3b8' }}
            formatter={(value: number) => [formatRatio(value), 'Ratio']}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Area
            type="monotone"
            dataKey="ratio"
            stroke={strokeColor}
            strokeWidth={2}
            fill="url(#ratioGradient)"
            dot={false}
            activeDot={{ r: 4, fill: strokeColor, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
