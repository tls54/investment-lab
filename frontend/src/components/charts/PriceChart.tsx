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
import { formatTimestamp, formatPrice } from '../../utils';
import type { HistoricalPrice } from '../../api/types';

interface PriceChartProps {
  data?: HistoricalPrice;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  height?: number;
  title?: string;
  timeRange?: number;
}

export function PriceChart({
  data,
  loading,
  error,
  onRetry,
  height = 400,
  title,
  timeRange,
}: PriceChartProps) {
  if (loading) {
    return (
      <Card title={title || 'Price History'}>
        <LoadingSpinner message="Loading chart data..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card title={title || 'Price History'}>
        <ErrorMessage error={error} onRetry={onRetry} />
      </Card>
    );
  }

  if (!data || data.prices.length === 0) {
    // Special message for Today/24H view with no data (likely non-trading day)
    const message = timeRange !== undefined && timeRange <= 1
      ? 'No trading data available for today. This may be a non-trading day for this market.'
      : 'No historical data available';

    return (
      <Card title={title || 'Price History'}>
        <div className="text-center py-12 text-text-muted">
          {message}
        </div>
      </Card>
    );
  }

  // For hourly data (1-7 days), show time; for daily data, show just date
  const showTime = timeRange !== undefined && timeRange <= 7;

  const chartData = data.prices.map((point) => ({
    timestamp: point.timestamp,
    price: point.close || point.price,
    date: showTime ? formatTimestamp(point.timestamp, 'long') : formatTimestamp(point.timestamp, 'date'),
  }));

  // Extract currency from the first price point (all should have the same currency)
  const currency = data.prices[0]?.currency || 'USD';

  const prices = chartData.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;

  // Determine if price went up or down
  const isPositive = chartData[chartData.length - 1].price >= chartData[0].price;
  const gradientColor = isPositive ? '#10b981' : '#ef4444';
  const strokeColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <Card
      title={title || `${data.symbol} Price History`}
      subtitle={`${data.count} data points`}
    >
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
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
            domain={[minPrice - padding, maxPrice + padding]}
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => formatPrice(value, currency)}
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
            formatter={(value: number) => [formatPrice(value, currency), 'Price']}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke={strokeColor}
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={false}
            activeDot={{ r: 4, fill: strokeColor, strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
