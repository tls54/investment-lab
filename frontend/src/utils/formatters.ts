const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: '$',
  GBP: '£',
  EUR: '€',
  BTC: '₿',
  ETH: 'Ξ',
};

export const formatPrice = (price: number, currency: string = 'USD'): string => {
  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' ';
  const decimals = price < 1 ? 6 : price < 100 ? 4 : 2;
  return `${symbol}${price.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
};

export const formatNumber = (num: number, decimals: number = 2): string => {
  return num.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatPercentChange = (change: number): { text: string; color: string } => {
  const sign = change >= 0 ? '+' : '';
  const color = change >= 0 ? 'text-green-600' : 'text-red-600';
  return {
    text: `${sign}${change.toFixed(2)}%`,
    color,
  };
};

export const formatTimestamp = (
  timestamp: string | Date,
  format: 'short' | 'long' | 'date' = 'short'
): string => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (format === 'short') {
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  }

  if (format === 'date') {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  }

  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

export const formatLargeNumber = (num: number): string => {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toString();
};

export const formatRatio = (ratio: number): string => {
  if (ratio < 0.0001) return ratio.toExponential(2);
  if (ratio < 1) return ratio.toFixed(6);
  if (ratio < 100) return ratio.toFixed(4);
  return ratio.toFixed(2);
};

/**
 * Extract currency from a symbol.
 * For crypto pairs like "BTC-USD", "ETH-GBP", extracts the currency (USD, GBP).
 * For stocks like "AAPL", defaults to USD.
 */
export const getCurrencyFromSymbol = (symbol: string): string => {
  if (symbol.includes('-')) {
    const parts = symbol.split('-');
    return parts[parts.length - 1]; // Get the last part after hyphen
  }
  return 'USD'; // Default to USD for stocks/ETFs
};
