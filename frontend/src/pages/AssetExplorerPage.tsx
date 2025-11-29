import { useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowRightLeft } from 'lucide-react';
import { SymbolSearch, PriceCard, DenominationPicker } from '../components/price';
import { PriceChart, RatioChart } from '../components/charts';
import { Card, Button } from '../components/common';
import { DateRangePicker } from '../components/common/DateRangePicker';
import {
  usePriceQuery,
  useHistoricalQuery,
  useConversionQuery,
  useHistoricalConversionQuery,
} from '../api/hooks';
import { REFRESH_INTERVALS, formatRatio, formatPrice, isCryptoDenomination, constructCryptoSymbol } from '../utils';

export default function AssetExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolParam = searchParams.get('symbol') || '';
  const denomParam = searchParams.get('denom') || 'NATIVE';

  const [symbol, setSymbol] = useState(symbolParam);
  const [denomination, setDenomination] = useState(denomParam || 'NATIVE');
  const [timeRange, setTimeRange] = useState(30);

  const updateParams = (newSymbol: string, newDenom: string) => {
    const params: Record<string, string> = {};
    if (newSymbol) params.symbol = newSymbol;
    if (newDenom && newDenom !== 'NATIVE') params.denom = newDenom;
    setSearchParams(params);
  };

  const handleSymbolChange = (newSymbol: string) => {
    setSymbol(newSymbol);
    if (newSymbol) {
      updateParams(newSymbol, denomination);
    }
  };

  const handleDenominationChange = (newDenom: string) => {
    setDenomination(newDenom);
    updateParams(symbol, newDenom);
  };

  const handleSwap = () => {
    if (symbol && denomination && denomination !== 'NATIVE') {
      const temp = symbol;
      setSymbol(denomination);
      setDenomination(temp);
      updateParams(denomination, temp);
    }
  };

  // API Queries
  const priceQuery = usePriceQuery(symbol || undefined, {
    refetchInterval: REFRESH_INTERVALS.PRICE,
  });

  const historicalQuery = useHistoricalQuery(
    symbol || undefined,
    { days: timeRange },
    !!symbol
  );

  // Construct the actual denomination symbol for crypto
  // If user selected "BTC" and asset is in GBP, use "BTC-GBP"
  // If user selected "BTC" and asset is in USD, use "BTC-USD"
  const actualDenomination = useMemo(() => {
    if (denomination === 'NATIVE') return undefined;

    // If denomination is a crypto symbol (BTC, ETH) and we have asset price data
    if (isCryptoDenomination(denomination) && priceQuery.data?.currency) {
      return constructCryptoSymbol(denomination, priceQuery.data.currency);
    }

    // Otherwise use denomination as-is (currency codes, other assets)
    return denomination;
  }, [denomination, priceQuery.data?.currency]);

  const conversionQuery = useConversionQuery(
    symbol || undefined,
    actualDenomination,
    !!symbol && !!actualDenomination
    // Smart crypto matching: BTC becomes BTC-GBP for GBP assets, BTC-USD for USD assets
    // This avoids unnecessary cross-currency conversion
  );

  const historicalConversionQuery = useHistoricalConversionQuery(
    symbol || undefined,
    actualDenomination,
    { days: timeRange },
    !!symbol && !!actualDenomination
    // Smart crypto matching applied to historical data as well
  );

  // Detect if conversion data is currency conversion or ratio conversion
  const isCurrencyConversion = conversionQuery.data && 'converted_price' in conversionQuery.data;
  const isRatioConversion = conversionQuery.data && 'ratio' in conversionQuery.data;

  // For ratio conversion, display the ratio
  // For currency conversion, we'll override the price display
  const displayRatio = isRatioConversion ? conversionQuery.data.ratio : undefined;

  // Get friendly display name for denomination
  const denominationDisplayName = useMemo(() => {
    if (!denomination || denomination === 'NATIVE') return undefined;

    // For crypto, show friendly name (Bitcoin, Ethereum) instead of symbol
    if (denomination === 'BTC') return 'Bitcoin';
    if (denomination === 'ETH') return 'Ethereum';

    // For other assets/currencies, use the symbol as-is
    return actualDenomination;
  }, [denomination, actualDenomination]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Asset Explorer</h1>
        <p className="text-text-muted mt-1">
          Search for any asset and view its price in different denominations
        </p>
      </div>

      {/* Search and Controls */}
      <Card>
        <div className="space-y-6">
          {/* Symbol Search */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 max-w-md">
              <SymbolSearch
                label="Asset Symbol"
                value={symbol}
                onChange={handleSymbolChange}
                placeholder="Search AAPL, BTC-USD, MSFT..."
              />
            </div>

            {/* Swap button (only when in ratio mode) */}
            {isRatioConversion && (
              <div className="flex items-end">
                <Button
                  variant="secondary"
                  onClick={handleSwap}
                  icon={<ArrowRightLeft className="w-4 h-4" />}
                >
                  Swap
                </Button>
              </div>
            )}
          </div>

          {/* Denomination Picker */}
          <DenominationPicker
            value={denomination}
            onChange={handleDenominationChange}
          />
        </div>
      </Card>

      {/* Price Display */}
      <PriceCard
        price={priceQuery.data}
        loading={priceQuery.isLoading}
        error={priceQuery.error}
        onRetry={() => priceQuery.refetch()}
        denominationSymbol={isRatioConversion ? denominationDisplayName : isCurrencyConversion ? (conversionQuery.data as any).target_currency : undefined}
        ratio={displayRatio}
        denominationCurrency={isRatioConversion ? denomination : isCurrencyConversion ? (conversionQuery.data as any).target_currency : undefined}
        currencyConversion={isCurrencyConversion ? conversionQuery.data as any : undefined}
        ratioConversion={isRatioConversion ? conversionQuery.data as any : undefined}
        lastUpdated={new Date()}
      />

      {/* Conversion Stats (when in ratio mode only) */}
      {isRatioConversion && conversionQuery.data && (
        <Card title="Conversion Details">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="stat-card">
              <span className="stat-label">Current Ratio</span>
              <span className="stat-value font-mono text-accent-blue">
                {formatRatio(conversionQuery.data.ratio)}
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Inverse Ratio</span>
              <span className="stat-value font-mono">
                {formatRatio(conversionQuery.data.inverse_ratio)}
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">{conversionQuery.data.asset_symbol} Price</span>
              <span className="stat-value font-mono">
                {formatPrice(conversionQuery.data.asset_price, conversionQuery.data.asset_currency)}
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">{conversionQuery.data.denomination_symbol} Price</span>
              <span className="stat-value font-mono">
                {formatPrice(conversionQuery.data.denomination_price, conversionQuery.data.denomination_currency)}
              </span>
            </div>
          </div>
        </Card>
      )}

      {/* Time Range Selector */}
      {symbol && (
        <Card>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <span className="text-sm font-medium text-text-secondary">
              Historical Data Range
            </span>
            <DateRangePicker
              selectedDays={timeRange}
              onDaysChange={setTimeRange}
            />
          </div>
        </Card>
      )}

      {/* Chart - Price, Ratio, or Currency depending on denomination */}
      {symbol && (
        <>
          {isRatioConversion ? (
            // Asset ratio conversion - show ratio chart
            <RatioChart
              data={historicalConversionQuery.data}
              loading={historicalConversionQuery.isLoading}
              error={historicalConversionQuery.error}
              onRetry={() => historicalConversionQuery.refetch()}
            />
          ) : isCurrencyConversion && historicalConversionQuery.data ? (
            // Currency conversion - transform data and show price chart
            <PriceChart
              data={{
                symbol: (historicalConversionQuery.data as any).symbol,
                asset_type: 'STOCK' as any,
                prices: (historicalConversionQuery.data as any).data.map((point: any) => ({
                  timestamp: point.timestamp,
                  price: point.converted_price,
                  close: point.close,
                  open: point.open,
                  high_24h: point.high,
                  low_24h: point.low,
                  volume: point.volume,
                  currency: point.target_currency,
                  source: 'yfinance',
                  asset_type: 'STOCK' as any,
                  symbol: (historicalConversionQuery.data as any).symbol,
                })),
                start_date: (historicalConversionQuery.data as any).start_date,
                end_date: (historicalConversionQuery.data as any).end_date,
                interval: (historicalConversionQuery.data as any).interval,
                count: (historicalConversionQuery.data as any).count,
              }}
              loading={historicalConversionQuery.isLoading}
              error={historicalConversionQuery.error}
              onRetry={() => historicalConversionQuery.refetch()}
            />
          ) : (
            // Native price - show price chart
            <PriceChart
              data={historicalQuery.data}
              loading={historicalQuery.isLoading}
              error={historicalQuery.error}
              onRetry={() => historicalQuery.refetch()}
            />
          )}
        </>
      )}

      {/* Historical Stats (when in ratio mode only) */}
      {isRatioConversion && historicalConversionQuery.data?.summary && (
        <Card title="Period Statistics">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-dark-600 rounded-lg">
              <span className="text-xs text-text-muted uppercase block mb-1">Min Ratio</span>
              <span className="text-lg font-semibold text-loss font-mono">
                {formatRatio(historicalConversionQuery.data.summary.min_ratio)}
              </span>
            </div>
            <div className="text-center p-4 bg-dark-600 rounded-lg">
              <span className="text-xs text-text-muted uppercase block mb-1">Average</span>
              <span className="text-lg font-semibold text-text-primary font-mono">
                {formatRatio(historicalConversionQuery.data.summary.avg_ratio)}
              </span>
            </div>
            <div className="text-center p-4 bg-dark-600 rounded-lg">
              <span className="text-xs text-text-muted uppercase block mb-1">Max Ratio</span>
              <span className="text-lg font-semibold text-gain font-mono">
                {formatRatio(historicalConversionQuery.data.summary.max_ratio)}
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
