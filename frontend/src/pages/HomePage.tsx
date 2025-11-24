import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ArrowRightLeft, LineChart, Search } from 'lucide-react';
import { Card, Button, Input } from '../components/common';
import { POPULAR_SYMBOLS } from '../utils';

const features = [
  {
    icon: TrendingUp,
    title: 'Price Viewer',
    description: 'View real-time and historical prices for stocks, ETFs, and cryptocurrencies.',
    path: '/price',
    color: 'text-blue-600 bg-blue-100',
  },
  {
    icon: ArrowRightLeft,
    title: 'Asset Conversion',
    description: 'Price any asset in terms of another. View AAPL in BTC, SPY in gold, and more.',
    path: '/convert',
    color: 'text-green-600 bg-green-100',
  },
  {
    icon: LineChart,
    title: 'Forecast',
    description: 'Generate probabilistic price forecasts using Monte Carlo simulation.',
    path: '/forecast',
    color: 'text-purple-600 bg-purple-100',
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const [searchSymbol, setSearchSymbol] = useState('');

  const handleSearch = () => {
    if (searchSymbol.trim()) {
      navigate(`/price?symbol=${searchSymbol.toUpperCase()}`);
    }
  };

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Investment Lab
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          A financial analysis platform for viewing prices, comparing assets,
          and generating probabilistic forecasts.
        </p>

        {/* Quick Search */}
        <div className="max-w-md mx-auto">
          <div className="flex gap-2">
            <Input
              placeholder="Enter symbol (e.g., AAPL, BTC-USD)"
              value={searchSymbol}
              onChange={setSearchSymbol}
              icon={<Search className="w-5 h-5" />}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch}>
              Search
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Features
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Card
              key={feature.path}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              padding="lg"
            >
              <div
                onClick={() => navigate(feature.path)}
                className="text-center"
              >
                <div className={`inline-flex p-4 rounded-full ${feature.color} mb-4`}>
                  <feature.icon className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Popular Symbols */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Popular Symbols
        </h2>
        <div className="flex flex-wrap justify-center gap-3">
          {POPULAR_SYMBOLS.map((item) => (
            <button
              key={item.symbol}
              onClick={() => navigate(`/price?symbol=${item.symbol}`)}
              className="px-4 py-2 bg-white border border-gray-200 rounded-full hover:border-primary-500 hover:text-primary-600 transition-colors"
            >
              <span className="font-medium">{item.symbol}</span>
              <span className="text-gray-500 ml-2 text-sm">{item.name}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
