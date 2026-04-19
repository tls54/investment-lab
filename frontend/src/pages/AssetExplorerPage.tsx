import { useState, useMemo, useEffect } from 'react';
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
  const [maEnabled, setMaEnabled] = useState(false);
  const [maPeriod, setMaPeriod] = useState(20);
  const [debouncedMaPeriod, setDebouncedMaPeriod] = useState(20);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedMaPeriod(maPeriod), 400);
    return () => clearTimeout(timer);
  }, [maPeriod]);

  // Determine interval based on time range
  // Today/24H: 5-minute intervals for high resolution
  // 7 days: 30-minute intervals
  // 30 days: 1-hour intervals
  // 90+ days: daily data
  const interval = useMemo(() => {
    if (timeRange <= 1) return '5m';
    if (timeRange === 7) return '30m';
    if (timeRange === 30) return '1h';
    return '1d';
  }, [timeRange]);

  // --- Pass 1: compute queryDays before queries ---
  // We don't yet know asset_type, so use stock assumptions (conservative — crypto
  // will over-fetch slightly on the first render, then self-correct once data loads).
  const queryDays = useMemo(() => {
    if (!maEnabled) return timeRange;
    const intervalMinutes =
      interval === '5m' ? 5 : interval === '30m' ? 30 : interval === '1h' ? 60 : 1440;
    // Use the debounced period for warmup — fetches only what the current MA needs.
    // Intraday: inflate 4.5× for trading-hours-only data density.
    // Daily: inflate 1.5× for weekends/holidays.
    // Cap: 730 days for daily (2 years) so long-range views still have warmup room;
    //      365 days for intraday (warmup is already small in calendar-day terms).
    const rawWarmupDays = Math.ceil((debouncedMaPeriod * intervalMinutes) / 1440);
    const warmupDays = interval !== '1d'
      ? Math.max(1, Math.ceil(rawWarmupDays * 4.5))
      : Math.max(1, Math.ceil(rawWarmupDays * 1.5));
    const cap = interval === '1d' ? 730 : 365;
    return Math.min(timeRange + warmupDays, cap);
  }, [maEnabled, timeRange, interval, debouncedMaPeriod]);

  // Conversion queries always use daily interval. The backend's ratio conversion
  // matches asset/denomination prices by calendar date, making sub-daily intervals
  // meaningless (denomination price is effectively daily regardless of interval).
  // Currency conversion forex rates are also daily in practice.
  const conversionQueryDays = useMemo(() => {
    if (!maEnabled) return timeRange;
    const warmupDays = Math.max(1, Math.ceil(debouncedMaPeriod * 1.5));
    return Math.min(timeRange + warmupDays, 730);
  }, [maEnabled, timeRange, debouncedMaPeriod]);

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
    { days: queryDays, interval },
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
  );

  const historicalConversionQuery = useHistoricalConversionQuery(
    symbol || undefined,
    actualDenomination,
    { days: conversionQueryDays, interval },
    !!symbol && !!actualDenomination
  );

  // --- Pass 2: compute MA constraints using loaded data ---
  const isCrypto = priceQuery.data?.asset_type === 'crypto';

  // Use actual loaded data count when available — this correctly handles early
  // trading-day (sparse today data), crypto 24/7, and non-standard market hours.
  // Falls back to a formula-based estimate before data loads.
  const estimatedDisplayPoints = useMemo(() => {
    const loadedCount = historicalQuery.data?.prices?.length
      ?? (historicalConversionQuery.data as any)?.data?.length;
    if (loadedCount !== undefined) return loadedCount;

    const hoursPerDay = isCrypto ? 24 : 8;
    const daysPerWeek = isCrypto ? 7 : 5;
    const days = timeRange === 0 ? 1 : timeRange;
    const activeDays = days * (daysPerWeek / 7);
    if (interval === '5m')  return Math.round(activeDays * hoursPerDay * 12);
    if (interval === '30m') return Math.round(activeDays * hoursPerDay * 2);
    if (interval === '1h')  return Math.round(activeDays * hoursPerDay);
    return Math.round(activeDays);
  }, [timeRange, interval, isCrypto, historicalQuery.data, historicalConversionQuery.data]);

  // Cap at 75% of display points (so MA line covers most of the chart) and hard-cap at 200.
  const maxMaPeriod = Math.min(200, Math.max(2, Math.floor(estimatedDisplayPoints * 0.75)));

  // Clamp maPeriod state when maxMaPeriod shrinks (e.g. switching to shorter time range)
  useEffect(() => {
    if (maPeriod > maxMaPeriod) setMaPeriod(maxMaPeriod);
  }, [maxMaPeriod]);

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
                onSubmit={handleSymbolChange}
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
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <span className="text-sm font-medium text-text-secondary">
                Historical Data Range
              </span>
              <DateRangePicker
                selectedDays={timeRange}
                onDaysChange={setTimeRange}
              />
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 pt-1 border-t border-border">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-text-secondary">Moving Average</span>
                <button
                  onClick={() => setMaEnabled(!maEnabled)}
                  className={`relative inline-flex h-5 w-9 flex-shrink-0 items-center rounded-full transition-colors focus:outline-none ${
                    maEnabled ? 'bg-accent-blue' : 'bg-dark-500'
                  }`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                      maEnabled ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              {maEnabled && (
                <div className="flex items-center gap-3 flex-1">
                  <input
                    type="range"
                    min={2}
                    max={maxMaPeriod}
                    value={Math.min(maPeriod, maxMaPeriod)}
                    onChange={(e) => setMaPeriod(Number(e.target.value))}
                    className="flex-1 accent-amber-400"
                  />
                  <span className="text-sm font-mono text-text-secondary w-32 text-right">
                    {Math.min(maPeriod, maxMaPeriod)}/{maxMaPeriod}{' '}
                    <span className="text-text-muted">
                      {interval === '5m' ? '5min' : interval === '30m' ? '30min' : interval === '1h' ? '1hr' : '1day'}
                    </span>
                  </span>
                </div>
              )}
            </div>
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
              timeRange={timeRange}
              maEnabled={maEnabled}
              maPeriod={Math.min(debouncedMaPeriod, maxMaPeriod)}
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
              timeRange={timeRange}
              maEnabled={maEnabled}
              maPeriod={Math.min(debouncedMaPeriod, maxMaPeriod)}
            />
          ) : (
            // Native price - show price chart
            <PriceChart
              data={historicalQuery.data}
              loading={historicalQuery.isLoading}
              error={historicalQuery.error}
              onRetry={() => historicalQuery.refetch()}
              timeRange={timeRange}
              maEnabled={maEnabled}
              maPeriod={Math.min(debouncedMaPeriod, maxMaPeriod)}
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
