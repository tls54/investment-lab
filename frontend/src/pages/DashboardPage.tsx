import { useNavigate } from 'react-router-dom';
import { LineChart, TrendingUp, ArrowRight, Search } from 'lucide-react';
import { useState } from 'react';
import { Card, Button, Input } from '../components/common';
import { usePriceQuery } from '../api/hooks';
import { formatPrice, POPULAR_SYMBOLS } from '../utils';

function QuickPriceCard({ symbol, name }: { symbol: string; name: string }) {
  const navigate = useNavigate();
  const { data, isLoading } = usePriceQuery(symbol);

  const change = data?.open && data?.close
    ? ((data.close - data.open) / data.open) * 100
    : 0;
  const isPositive = change >= 0;

  return (
    <div
      onClick={() => navigate(`/explore?symbol=${symbol}`)}
      className="card-hover p-4 cursor-pointer"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-text-primary">{symbol}</span>
        {!isLoading && data && (
          <span className={`text-xs px-2 py-0.5 rounded ${
            isPositive ? 'bg-gain/10 text-gain' : 'bg-loss/10 text-loss'
          }`}>
            {isPositive ? '+' : ''}{change.toFixed(2)}%
          </span>
        )}
      </div>
      <div className="text-xs text-text-muted mb-1">{name}</div>
      {isLoading ? (
        <div className="h-6 bg-dark-600 rounded animate-pulse" />
      ) : data ? (
        <div className="text-lg font-bold text-text-primary font-mono">
          {formatPrice(data.price, data.currency)}
        </div>
      ) : null}
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [searchValue, setSearchValue] = useState('');

  const handleSearch = () => {
    if (searchValue.trim()) {
      navigate(`/explore?symbol=${searchValue.toUpperCase()}`);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Dashboard</h1>
        <p className="text-text-muted mt-1">
          Financial analysis platform with real-time data and forecasting
        </p>
      </div>

      {/* Quick Search */}
      <Card>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Quick search... (e.g., AAPL, BTC-USD)"
              value={searchValue}
              onChange={setSearchValue}
              icon={<Search className="w-5 h-5" />}
              size="lg"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button size="lg" onClick={handleSearch}>
            Search
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </Card>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card
          hover
          className="group"
          padding="lg"
        >
          <div onClick={() => navigate('/explore')} className="cursor-pointer">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-accent-blue/10 flex items-center justify-center group-hover:bg-accent-blue/20 transition-colors">
                <LineChart className="w-6 h-6 text-accent-blue" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Asset Explorer</h3>
                <p className="text-sm text-text-muted">View prices and convert between assets</p>
              </div>
            </div>
            <ul className="text-sm text-text-secondary space-y-2">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-blue" />
                Real-time price data for stocks, crypto, ETFs
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-blue" />
                Convert prices to any denomination (BTC, GLD, etc.)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-blue" />
                Historical charts with customizable date ranges
              </li>
            </ul>
          </div>
        </Card>

        <Card
          hover
          className="group"
          padding="lg"
        >
          <div onClick={() => navigate('/forecast')} className="cursor-pointer">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-xl bg-accent-purple/10 flex items-center justify-center group-hover:bg-accent-purple/20 transition-colors">
                <TrendingUp className="w-6 h-6 text-accent-purple" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary">Price Forecast</h3>
                <p className="text-sm text-text-muted">Monte Carlo simulation with GBM</p>
              </div>
            </div>
            <ul className="text-sm text-text-secondary space-y-2">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" />
                Probabilistic price forecasts (up to 90 days)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" />
                Risk metrics: VaR, CVaR, probability of gain
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-purple" />
                GPU-accelerated simulation (up to 100K paths)
              </li>
            </ul>
          </div>
        </Card>
      </div>

      {/* Popular Assets */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Popular Assets</h2>
          <Button variant="ghost" size="sm" onClick={() => navigate('/explore')}>
            View All
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {POPULAR_SYMBOLS.slice(0, 5).map((item) => (
            <QuickPriceCard key={item.symbol} symbol={item.symbol} name={item.name} />
          ))}
        </div>
      </div>
    </div>
  );
}
