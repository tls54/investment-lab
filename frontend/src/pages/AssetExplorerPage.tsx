import { useState } from 'react';
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
import { REFRESH_INTERVALS, formatRatio, formatPrice } from '../utils';

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

  const conversionQuery = useConversionQuery(
    symbol || undefined,
    denomination !== 'NATIVE' ? denomination : undefined,
    !!symbol && denomination !== 'NATIVE'
    // Note: Not passing currency parameters - defaults to USD on backend
    // This ensures consistent behavior across all assets and denominations
  );

  const historicalConversionQuery = useHistoricalConversionQuery(
    symbol || undefined,
    denomination !== 'NATIVE' ? denomination : undefined,
    { days: timeRange },
    !!symbol && denomination !== 'NATIVE'
    // Note: Not passing currency parameters - defaults to USD on backend
  );

  const showRatioMode = denomination !== 'NATIVE' && !!symbol;
  const displayRatio = showRatioMode && conversionQuery.data ? conversionQuery.data.ratio : undefined;

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

            {/* Swap button (only when not USD) */}
            {showRatioMode && (
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
        denominationSymbol={showRatioMode ? denomination : undefined}
        ratio={displayRatio}
        denominationCurrency={showRatioMode ? denomination.split('-')[0] : undefined}
        lastUpdated={new Date()}
      />

      {/* Conversion Stats (when in ratio mode) */}
      {showRatioMode && conversionQuery.data && (
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
                {formatPrice(conversionQuery.data.asset_price_usd, 'USD')}
              </span>
            </div>
            <div className="stat-card">
              <span className="stat-label">{conversionQuery.data.denomination_symbol} Price</span>
              <span className="stat-value font-mono">
                {formatPrice(conversionQuery.data.denomination_price_usd, 'USD')}
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

      {/* Chart - either Price or Ratio depending on denomination */}
      {symbol && (
        <>
          {showRatioMode ? (
            <RatioChart
              data={historicalConversionQuery.data}
              loading={historicalConversionQuery.isLoading}
              error={historicalConversionQuery.error}
              onRetry={() => historicalConversionQuery.refetch()}
            />
          ) : (
            <PriceChart
              data={historicalQuery.data}
              loading={historicalQuery.isLoading}
              error={historicalQuery.error}
              onRetry={() => historicalQuery.refetch()}
            />
          )}
        </>
      )}

      {/* Historical Stats (when in ratio mode) */}
      {showRatioMode && historicalConversionQuery.data?.summary && (
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
