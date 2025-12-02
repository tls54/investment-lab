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
  timeRange?: number;
}

export function RatioChart({
  data,
  loading,
  error,
  onRetry,
  height = 400,
  timeRange,
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
    // Special message for Today/24H view with no data (likely non-trading day)
    const message = timeRange !== undefined && timeRange <= 1
      ? 'No trading data available for today. This may be a non-trading day for this market.'
      : 'No historical data available';

    return (
      <Card title="Ratio History">
        <div className="text-center py-12 text-text-muted">
          {message}
        </div>
      </Card>
    );
  }

  // For hourly data (1-7 days), show time; for daily data, show just date
  const showTime = timeRange !== undefined && timeRange <= 7;

  // Parse interval and calculate offset in milliseconds
  // Bars are timestamped at START, but we want to show the END (when close price occurs)
  const getIntervalOffset = (interval: string): number => {
    const match = interval.match(/^(\d+)([mhd])$/);
    if (!match) return 0;

    const value = parseInt(match[1]);
    const unit = match[2];

    if (unit === 'm') return value * 60 * 1000; // minutes to ms
    if (unit === 'h') return value * 60 * 60 * 1000; // hours to ms
    if (unit === 'd') return value * 24 * 60 * 60 * 1000; // days to ms
    return 0;
  };

  const intervalOffset = getIntervalOffset(data.interval);

  const chartData = data.data.map((point) => {
    // Shift timestamp to end of period (when close price occurs)
    const adjustedTimestamp = new Date(new Date(point.timestamp).getTime() + intervalOffset);

    return {
      timestamp: adjustedTimestamp.toISOString(),
      ratio: point.ratio,
      date: showTime ? formatTimestamp(adjustedTimestamp, 'long') : formatTimestamp(adjustedTimestamp, 'date'),
    };
  });

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
            minTickGap={50}
            interval="preserveStartEnd"
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
