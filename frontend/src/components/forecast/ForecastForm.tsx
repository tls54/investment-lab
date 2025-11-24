import { useState } from 'react';
import { Play, Settings, ChevronDown, ChevronUp, Zap } from 'lucide-react';
import { SymbolSearch } from '../price';
import { Card, Button, Input } from '../common';
import { PATH_COUNTS, DEFAULT_FORECAST_CONFIG } from '../../utils';
import type { ForecastRequest } from '../../api/types';

interface ForecastFormProps {
  onSubmit: (config: ForecastRequest) => void;
  loading?: boolean;
  initialSymbol?: string;
}

export function ForecastForm({ onSubmit, loading, initialSymbol = '' }: ForecastFormProps) {
  const [symbol, setSymbol] = useState(initialSymbol);
  const [horizonDays, setHorizonDays] = useState<number>(DEFAULT_FORECAST_CONFIG.horizon_days);
  const [nPaths, setNPaths] = useState<number>(DEFAULT_FORECAST_CONFIG.n_paths);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [calibrationDays, setCalibrationDays] = useState<number>(DEFAULT_FORECAST_CONFIG.calibration_days);
  const [includePaths, setIncludePaths] = useState<boolean>(DEFAULT_FORECAST_CONFIG.include_paths);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol) return;

    onSubmit({
      symbol,
      horizon_days: horizonDays,
      n_paths: nPaths,
      calibration_days: calibrationDays,
      include_paths: includePaths,
      n_sample_paths: 100,
    });
  };

  return (
    <Card title="Forecast Configuration" subtitle="Configure Monte Carlo simulation parameters">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Symbol Search */}
        <div className="max-w-md">
          <SymbolSearch
            label="Asset Symbol"
            value={symbol}
            onChange={setSymbol}
            placeholder="e.g., AAPL, MSFT, BTC-USD"
          />
        </div>

        {/* Horizon Days Slider */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-text-secondary">
              Forecast Horizon
            </label>
            <span className="text-lg font-bold text-accent-purple font-mono">
              {horizonDays} days
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="90"
            value={horizonDays}
            onChange={(e) => setHorizonDays(Number(e.target.value))}
            className="w-full h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none
                       [&::-webkit-slider-thumb]:w-4
                       [&::-webkit-slider-thumb]:h-4
                       [&::-webkit-slider-thumb]:rounded-full
                       [&::-webkit-slider-thumb]:bg-accent-purple
                       [&::-webkit-slider-thumb]:cursor-pointer
                       [&::-webkit-slider-thumb]:shadow-glow-purple"
          />
          <div className="flex justify-between text-xs text-text-muted mt-2">
            <span>1 day</span>
            <span>30 days</span>
            <span>60 days</span>
            <span>90 days</span>
          </div>
        </div>

        {/* Simulation Paths */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-3">
            Simulation Paths
          </label>
          <div className="flex gap-2 flex-wrap">
            {PATH_COUNTS.map((count) => (
              <button
                key={count.value}
                type="button"
                onClick={() => setNPaths(count.value)}
                className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                  nPaths === count.value
                    ? 'bg-accent-purple text-white shadow-glow-purple'
                    : 'bg-dark-600 text-text-secondary hover:text-text-primary hover:bg-dark-500 border border-dark-500'
                }`}
              >
                {count.label}
                {count.value >= 50000 && (
                  <Zap className="w-3 h-3 inline ml-1 text-yellow-400" />
                )}
              </button>
            ))}
          </div>
          <p className="text-xs text-text-muted mt-2">
            More paths = higher accuracy but slower. 10K recommended for most cases.
          </p>
        </div>

        {/* Advanced Options Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-accent-blue hover:text-accent-cyan transition-colors"
          >
            <Settings className="w-4 h-4" />
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
            {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>

        {/* Advanced Options Panel */}
        {showAdvanced && (
          <div className="space-y-4 p-4 bg-dark-700 rounded-lg border border-dark-600">
            <div className="max-w-xs">
              <Input
                label="Calibration Period (days)"
                type="number"
                value={calibrationDays.toString()}
                onChange={(val) => setCalibrationDays(Number(val) || 252)}
                hint="Historical data used for model calibration. Default: 252 (1 year)"
              />
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="includePaths"
                checked={includePaths}
                onChange={(e) => setIncludePaths(e.target.checked)}
                className="w-4 h-4 rounded border-dark-500 bg-dark-600 text-accent-purple
                           focus:ring-accent-purple focus:ring-offset-dark-800"
              />
              <label htmlFor="includePaths" className="text-sm text-text-secondary">
                Include sample paths for visualization (enables distribution chart)
              </label>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <Button
          type="submit"
          size="lg"
          loading={loading}
          disabled={!symbol || loading}
          className="w-full md:w-auto"
          icon={<Play className="w-4 h-4" />}
        >
          Generate Forecast
        </Button>
      </form>
    </Card>
  );
}
