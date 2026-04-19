import {
  AreaChart,
  Area,
  Line,
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
  maEnabled?: boolean;
  maPeriod?: number;
}

export function RatioChart({
  data,
  loading,
  error,
  onRetry,
  height = 400,
  timeRange,
  maEnabled = false,
  maPeriod = 20,
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

  const getIntervalOffset = (interval: string): number => {
    const match = interval.match(/^(\d+)([mhd])$/);
    if (!match) return 0;
    const value = parseInt(match[1]);
    const unit = match[2];
    if (unit === 'm') return value * 60 * 1000;
    if (unit === 'h') return value * 60 * 60 * 1000;
    if (unit === 'd') return value * 24 * 60 * 60 * 1000;
    return 0;
  };

  const intervalOffset = getIntervalOffset(data.interval);

  // Map to chart points with adjusted timestamps
  const chartData = data.data.map((point) => {
    const adjustedTimestamp = new Date(new Date(point.timestamp).getTime() + intervalOffset);
    return {
      timestamp: adjustedTimestamp.toISOString(),
      ratio: point.ratio,
      date: showTime ? formatTimestamp(adjustedTimestamp, 'long') : formatTimestamp(adjustedTimestamp, 'date'),
    };
  });

  // Compute MA over the full dataset (including any warmup points before the display window)
  const fullData = chartData.map((d, i) => {
    let ma: number | null = null;
    if (maEnabled && i >= maPeriod - 1) {
      const slice = chartData.slice(i - maPeriod + 1, i + 1);
      ma = slice.reduce((sum, p) => sum + p.ratio, 0) / maPeriod;
    }
    return { ...d, ma };
  });

  // Filter to the display window — warmup points stay hidden
  const rawDisplay = (() => {
    if (!maEnabled || timeRange === undefined) return fullData;
    if (timeRange === 0) {
      const now = new Date();
      const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      return fullData.filter((d) => new Date(d.timestamp) >= midnight);
    }
    const cutoff = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);
    return fullData.filter((d) => new Date(d.timestamp) >= cutoff);
  })();
  const displayData = rawDisplay.length > 0 ? rawDisplay : fullData;

  const ratios = displayData.map((d) => d.ratio);
  const maVals = maEnabled
    ? displayData.map((d) => d.ma).filter((v): v is number => v !== null)
    : [];
  const minRatio = Math.min(...ratios, ...maVals);
  const maxRatio = Math.max(...ratios, ...maVals);
  const padding = (maxRatio - minRatio) * 0.1;

  const isPositive = displayData[displayData.length - 1].ratio >= displayData[0].ratio;
  const gradientColor = isPositive ? '#10b981' : '#ef4444';
  const strokeColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <Card
      title={`${data.asset_symbol} / ${data.denomination_symbol}`}
      subtitle={`${displayData.length} data points`}
    >
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={displayData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
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
            formatter={(value: number, name: string) => {
              if (name === 'ma') return [formatRatio(value), `MA(${maPeriod})`];
              return [formatRatio(value), 'Ratio'];
            }}
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
          {maEnabled && (
            <Line
              type="monotone"
              dataKey="ma"
              stroke="#f59e0b"
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, fill: '#f59e0b', strokeWidth: 0 }}
              connectNulls={false}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
