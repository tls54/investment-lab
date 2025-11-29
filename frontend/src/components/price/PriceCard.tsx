import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { Card, LoadingSpinner, ErrorMessage, Button } from '../common';
import { formatPrice, formatTimestamp } from '../../utils';
import type { Price } from '../../api/types';

interface CurrencyConversion {
  converted_price: number;
  target_currency: string;
  native_price: number;
  native_currency: string;
  forex_rate: number;
  conversion_method: string;
}

interface RatioConversion {
  conversion_method: 'direct' | 'triangular';
  common_currency?: string;
  asset_currency: string;
  denomination_currency: string;
}

interface PriceCardProps {
  price?: Price;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  denominationSymbol?: string;
  ratio?: number;
  denominationCurrency?: string;
  currencyConversion?: CurrencyConversion;
  ratioConversion?: RatioConversion;
  lastUpdated?: Date;
}

export function PriceCard({
  price,
  loading,
  error,
  onRetry,
  denominationSymbol,
  ratio,
  denominationCurrency,
  currencyConversion,
  ratioConversion,
  lastUpdated,
}: PriceCardProps) {
  if (loading && !price) {
    return (
      <Card>
        <LoadingSpinner message="Fetching price data..." />
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <ErrorMessage error={error} onRetry={onRetry} />
      </Card>
    );
  }

  if (!price) {
    return (
      <Card>
        <div className="text-center py-12">
          <p className="text-text-muted">Enter a symbol to view price data</p>
        </div>
      </Card>
    );
  }

  // Determine what price to display
  const displayPrice = currencyConversion
    ? currencyConversion.converted_price
    : ratio !== undefined
      ? ratio
      : price.price;

  const displayCurrency = currencyConversion
    ? currencyConversion.target_currency
    : denominationCurrency
      ? denominationCurrency
      : price.currency;

  const hasChange = price.open && price.close;
  const change = hasChange ? ((price.close! - price.open!) / price.open!) * 100 : 0;
  const isPositive = change >= 0;

  return (
    <Card>
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
        {/* Left: Symbol and Price */}
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-2xl font-bold text-text-primary">{price.symbol}</h2>
            <span className="px-2.5 py-1 bg-dark-500 text-text-secondary text-xs font-medium rounded-md uppercase">
              {price.asset_type}
            </span>
            {loading && (
              <RefreshCw className="w-4 h-4 text-accent-blue animate-spin" />
            )}
          </div>

          <div className="flex items-baseline gap-4 mb-4">
            <span className="text-4xl font-bold text-text-primary font-mono">
              {formatPrice(displayPrice, displayCurrency)}
            </span>
            {hasChange && (
              <div
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg ${
                  isPositive ? 'bg-gain/10 text-gain' : 'bg-loss/10 text-loss'
                }`}
              >
                {isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span className="font-semibold">
                  {isPositive ? '+' : ''}{change.toFixed(2)}%
                </span>
              </div>
            )}
          </div>

          {currencyConversion && (
            <p className="text-sm text-text-muted">
              Converted to {currencyConversion.target_currency}
              {currencyConversion.conversion_method === 'forex' && (
                <span> (1 {currencyConversion.native_currency} = {currencyConversion.forex_rate.toFixed(4)} {currencyConversion.target_currency})</span>
              )}
            </p>
          )}

          {ratio !== undefined && denominationSymbol && !currencyConversion && (
            <div className="text-sm text-text-muted">
              <p>Priced in {denominationSymbol}</p>
              {ratioConversion?.conversion_method === 'triangular' && ratioConversion.common_currency && (
                <p className="text-xs mt-1 text-text-muted/80">
                  Cross-currency conversion via {ratioConversion.common_currency} ({ratioConversion.asset_currency} → {ratioConversion.common_currency} → ratio with {ratioConversion.denomination_currency})
                </p>
              )}
            </div>
          )}
        </div>

        {/* Right: Stats */}
        <div className="grid grid-cols-2 gap-4 lg:min-w-[200px]">
          {price.volume && (
            <div>
              <span className="text-xs text-text-muted uppercase">Volume</span>
              <p className="text-sm font-medium text-text-primary">
                {price.volume.toLocaleString()}
              </p>
            </div>
          )}
          {price.open && (
            <div>
              <span className="text-xs text-text-muted uppercase">Open</span>
              <p className="text-sm font-medium text-text-primary font-mono">
                {formatPrice(price.open, price.currency)}
              </p>
            </div>
          )}
          {price.high_24h && (
            <div>
              <span className="text-xs text-text-muted uppercase">High</span>
              <p className="text-sm font-medium text-gain font-mono">
                {formatPrice(price.high_24h, price.currency)}
              </p>
            </div>
          )}
          {price.low_24h && (
            <div>
              <span className="text-xs text-text-muted uppercase">Low</span>
              <p className="text-sm font-medium text-loss font-mono">
                {formatPrice(price.low_24h, price.currency)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
        <span className="text-xs text-text-muted">
          Source: {price.source}
        </span>
        <span className="text-xs text-text-muted">
          Updated {formatTimestamp(lastUpdated || price.timestamp)}
        </span>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry} icon={<RefreshCw className="w-4 h-4" />}>
            Refresh
          </Button>
        )}
      </div>
    </Card>
  );
}
