# Investment Lab - Frontend Specification

## Document Purpose
This document provides complete specifications for building the Investment Lab frontend. It is designed for an AI coding assistant (Claude Code) to implement the entire frontend without human intervention.

**Target Audience:** Claude Code (AI implementation agent)  
**Implementation Style:** Step-by-step, production-ready, best practices  
**Expected Outcome:** Fully functional React application connected to existing backend

---

## Project Overview

### What We're Building
A financial analysis web application that allows users to:
1. View current prices for stocks, ETFs, and cryptocurrencies
2. Price assets in arbitrary denominations (e.g., AAPL in BTC, not just USD)
3. View historical price ratios between any two assets
4. Generate probabilistic price forecasts using Monte Carlo simulation
5. Visualize forecast distributions and risk metrics

### What Makes This Unique
- **Denominational pricing:** View any asset priced in any other asset (AAPL/BTC, SPY/GLD, etc.)
- **Probabilistic forecasts:** Not just "price goes up/down" but full distribution of outcomes
- **GPU-accelerated:** Backend uses PyTorch for fast Monte Carlo simulation
- **No API keys required:** All data via yfinance (free, unlimited)

### Backend Status
✅ **FULLY FUNCTIONAL** - All APIs tested and working:
- Current prices
- Historical data
- Denomination conversion
- GBM forecasting
- Running at: `http://localhost:8000`
- Interactive docs at: `http://localhost:8000/docs`

---

## Tech Stack Requirements

### Core Framework
```json
{
  "framework": "React 18",
  "language": "TypeScript 5",
  "build_tool": "Vite",
  "package_manager": "npm"
}
```

### UI & Styling
```json
{
  "css_framework": "Tailwind CSS",
  "component_library": "shadcn/ui (optional, for complex components)",
  "icons": "lucide-react",
  "fonts": "Inter (from Google Fonts)"
}
```

### Data & State Management
```json
{
  "api_client": "TanStack Query (React Query)",
  "http_client": "axios",
  "form_handling": "React Hook Form (optional)",
  "state": "React Context (for simple global state)"
}
```

### Charts & Visualization
```json
{
  "primary_charts": "recharts (easier) OR lightweight-charts (more powerful)",
  "distribution_plots": "recharts (histogram, area charts)",
  "recommendation": "Start with recharts, migrate to lightweight-charts if needed"
}
```

### Development Tools
```json
{
  "linting": "ESLint",
  "formatting": "Prettier",
  "type_checking": "TypeScript strict mode"
}
```

---

## Project Structure

```
frontend/
├── public/
│   └── vite.svg                    # Favicon (can replace)
├── src/
│   ├── api/                        # API client & hooks
│   │   ├── client.ts               # Axios instance with base config
│   │   ├── endpoints.ts            # API endpoint definitions
│   │   ├── types.ts                # TypeScript types for API responses
│   │   └── hooks/                  # React Query hooks
│   │       ├── usePriceQuery.ts
│   │       ├── useHistoricalQuery.ts
│   │       ├── useConversionQuery.ts
│   │       └── useForecastMutation.ts
│   ├── components/                 # React components
│   │   ├── layout/
│   │   │   ├── Header.tsx          # Top navigation
│   │   │   ├── Sidebar.tsx         # Optional side navigation
│   │   │   └── Layout.tsx          # Main layout wrapper
│   │   ├── price/
│   │   │   ├── PriceCard.tsx       # Display current price
│   │   │   ├── SymbolSearch.tsx    # Symbol input/search
│   │   │   └── DenominationPicker.tsx  # USD/BTC/GBP selector
│   │   ├── charts/
│   │   │   ├── PriceChart.tsx      # Historical price line chart
│   │   │   ├── RatioChart.tsx      # Asset/denomination ratio chart
│   │   │   ├── ForecastChart.tsx   # Forecast with confidence bands
│   │   │   └── DistributionChart.tsx  # Histogram of forecast outcomes
│   │   ├── forecast/
│   │   │   ├── ForecastForm.tsx    # Configure forecast parameters
│   │   │   ├── ForecastResults.tsx # Display forecast statistics
│   │   │   ├── RiskMetrics.tsx     # VaR, CVaR, probability display
│   │   │   └── ConfidenceIntervals.tsx  # P05, P50, P95 display
│   │   └── common/
│   │       ├── Button.tsx          # Reusable button
│   │       ├── Input.tsx           # Reusable input
│   │       ├── Card.tsx            # Card container
│   │       ├── LoadingSpinner.tsx  # Loading state
│   │       └── ErrorMessage.tsx    # Error display
│   ├── pages/                      # Page components (views)
│   │   ├── HomePage.tsx            # Landing/dashboard
│   │   ├── PriceViewerPage.tsx     # Current + historical prices
│   │   ├── ConversionPage.tsx      # Denomination conversion tool
│   │   ├── ForecastPage.tsx        # Forecast generator
│   │   └── NotFoundPage.tsx        # 404 page
│   ├── context/                    # React Context for global state
│   │   ├── SymbolContext.tsx       # Currently selected symbol
│   │   └── DenominationContext.tsx # Currently selected denomination
│   ├── utils/                      # Utility functions
│   │   ├── formatters.ts           # Number/date formatting
│   │   ├── validators.ts           # Input validation
│   │   └── constants.ts            # App constants
│   ├── types/                      # Shared TypeScript types
│   │   └── index.ts                # All type definitions
│   ├── App.tsx                     # Root component
│   ├── main.tsx                    # Entry point
│   ├── index.css                   # Global styles + Tailwind imports
│   └── vite-env.d.ts               # Vite type definitions
├── .env.development                # Environment variables (API URL)
├── .eslintrc.cjs                   # ESLint configuration
├── .prettierrc                     # Prettier configuration
├── index.html                      # HTML template
├── package.json                    # Dependencies
├── postcss.config.js               # PostCSS for Tailwind
├── tailwind.config.js              # Tailwind configuration
├── tsconfig.json                   # TypeScript configuration
├── tsconfig.node.json              # TypeScript for Node scripts
├── vite.config.ts                  # Vite configuration
└── README.md                       # Frontend-specific README
```

---

## API Integration Specifications

### Base Configuration

**File: `src/api/client.ts`**
```typescript
import axios from 'axios';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds (forecasts can be slow)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging (optional)
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### TypeScript Types

**File: `src/api/types.ts`**
```typescript
// ============================================================================
// API Response Types (must match backend Pydantic models)
// ============================================================================

export interface Price {
  symbol: string;
  asset_type: 'stock' | 'crypto' | 'commodity' | 'forex';
  price: number;
  timestamp: string; // ISO datetime
  volume?: number;
  currency: string;
  source: string;
}

export interface PricePoint {
  timestamp: string; // ISO datetime
  price: number;
  volume?: number;
}

export interface HistoricalPrice {
  symbol: string;
  asset_type: 'stock' | 'crypto' | 'commodity' | 'forex';
  prices: PricePoint[];
  start_date: string; // ISO date
  end_date: string; // ISO date
  interval: string;
}

export interface ConversionResult {
  asset: string;
  denomination: string;
  ratio: number; // asset/denomination
  inverse_ratio: number; // denomination/asset
  timestamp: string;
  asset_price: Price;
  denomination_price: Price;
}

export interface HistoricalConversion {
  asset: string;
  denomination: string;
  ratios: Array<{
    timestamp: string;
    ratio: number;
    inverse_ratio: number;
  }>;
  summary: {
    min_ratio: number;
    max_ratio: number;
    avg_ratio: number;
    current_ratio: number;
  };
  start_date: string;
  end_date: string;
}

export interface ForecastRequest {
  symbol: string;
  horizon_days: number;
  n_paths?: number; // default: 10000
  calibration_days?: number; // default: 252
  include_paths?: boolean; // default: false
  n_sample_paths?: number; // default: 100
}

export interface ForecastResponse {
  symbol: string;
  current_price: number;
  horizon_days: number;
  n_paths: number;
  
  // Forecast statistics
  mean: number;
  median: number;
  std: number;
  percentiles: {
    p05: number;
    p25: number;
    p50: number;
    p75: number;
    p95: number;
  };
  
  // Risk metrics
  var_95: number; // Value at Risk
  cvar_95: number; // Conditional VaR
  probability_above_current: number; // 0-1
  expected_return: number; // percentage
  
  // Model info
  parameters: {
    mu: number;
    sigma: number;
    S0: number;
    interpretation: {
      annual_return: string;
      annual_volatility: string;
      initial_price: string;
    };
  };
  
  calibration_period: {
    start: string;
    end: string;
    days: number;
  };
  
  // Optional: sample paths for visualization
  sample_paths?: number[][]; // each inner array is a path
}

// ============================================================================
// API Error Types
// ============================================================================

export interface APIError {
  detail: string;
  status?: number;
}

// ============================================================================
// Query Parameter Types
// ============================================================================

export interface HistoricalQueryParams {
  days?: number;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
}

export interface ForecastQueryParams {
  days?: number; // shortcut for horizon_days
}
```

### API Endpoints

**File: `src/api/endpoints.ts`**
```typescript
import apiClient from './client';
import type {
  Price,
  HistoricalPrice,
  ConversionResult,
  HistoricalConversion,
  ForecastRequest,
  ForecastResponse,
  HistoricalQueryParams,
  ForecastQueryParams,
} from './types';

// ============================================================================
// Price Endpoints
// ============================================================================

/**
 * Get current price for a symbol
 * 
 * @param symbol - Stock/ETF/Crypto symbol (e.g., "AAPL", "BTC-USD")
 * @returns Current price data
 * 
 * @example
 * const price = await getCurrentPrice("AAPL");
 * console.log(price.price); // 175.50
 */
export const getCurrentPrice = async (symbol: string): Promise<Price> => {
  const response = await apiClient.get<Price>(`/api/price/${symbol}`);
  return response.data;
};

/**
 * Get historical prices for a symbol
 * 
 * @param symbol - Stock/ETF/Crypto symbol
 * @param params - Query parameters (days OR start_date + end_date)
 * @returns Historical price data
 * 
 * @example
 * // Last 30 days
 * const history = await getHistoricalPrices("AAPL", { days: 30 });
 * 
 * // Custom date range
 * const history = await getHistoricalPrices("AAPL", {
 *   start_date: "2025-01-01",
 *   end_date: "2025-11-08"
 * });
 */
export const getHistoricalPrices = async (
  symbol: string,
  params: HistoricalQueryParams
): Promise<HistoricalPrice> => {
  const response = await apiClient.get<HistoricalPrice>(
    `/api/price/${symbol}/history`,
    { params }
  );
  return response.data;
};

// ============================================================================
// Conversion Endpoints
// ============================================================================

/**
 * Convert asset to denomination (current price)
 * 
 * @param asset - Asset symbol (e.g., "AAPL")
 * @param denomination - Denomination symbol (e.g., "BTC-USD")
 * @returns Conversion ratios and prices
 * 
 * @example
 * const conversion = await getCurrentConversion("AAPL", "BTC-USD");
 * console.log(conversion.ratio); // 0.00185 (AAPL costs 0.00185 BTC)
 */
export const getCurrentConversion = async (
  asset: string,
  denomination: string
): Promise<ConversionResult> => {
  const response = await apiClient.get<ConversionResult>(
    `/api/convert/${asset}/${denomination}`
  );
  return response.data;
};

/**
 * Get historical conversion ratios
 * 
 * @param asset - Asset symbol
 * @param denomination - Denomination symbol
 * @param params - Query parameters (days OR start_date + end_date)
 * @returns Historical ratio data with summary statistics
 * 
 * @example
 * const history = await getHistoricalConversion("AAPL", "BTC-USD", { days: 90 });
 * console.log(history.summary.avg_ratio);
 */
export const getHistoricalConversion = async (
  asset: string,
  denomination: string,
  params: HistoricalQueryParams
): Promise<HistoricalConversion> => {
  const response = await apiClient.get<HistoricalConversion>(
    `/api/convert/${asset}/${denomination}/history`,
    { params }
  );
  return response.data;
};

// ============================================================================
// Forecast Endpoints
// ============================================================================

/**
 * Get quick forecast with default parameters
 * 
 * @param symbol - Symbol to forecast
 * @param params - Query parameters (just horizon days)
 * @returns Forecast results
 * 
 * @example
 * const forecast = await getQuickForecast("AAPL", { days: 30 });
 * console.log(forecast.mean); // Expected price in 30 days
 */
export const getQuickForecast = async (
  symbol: string,
  params?: ForecastQueryParams
): Promise<ForecastResponse> => {
  const response = await apiClient.get<ForecastResponse>(
    `/api/forecast/gbm/${symbol}`,
    { params }
  );
  return response.data;
};

/**
 * Generate forecast with custom parameters
 * 
 * @param request - Full forecast configuration
 * @returns Forecast results with optional sample paths
 * 
 * @example
 * const forecast = await generateForecast({
 *   symbol: "AAPL",
 *   horizon_days: 30,
 *   n_paths: 50000,
 *   include_paths: true,
 *   n_sample_paths: 200
 * });
 */
export const generateForecast = async (
  request: ForecastRequest
): Promise<ForecastResponse> => {
  const response = await apiClient.post<ForecastResponse>(
    '/api/forecast/gbm',
    request
  );
  return response.data;
};
```

### React Query Hooks

**File: `src/api/hooks/usePriceQuery.ts`**
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { getCurrentPrice } from '../endpoints';
import type { Price } from '../types';

/**
 * Hook for fetching current price
 * 
 * @param symbol - Symbol to fetch (disabled if undefined)
 * @param options - React Query options (refetchInterval, etc.)
 * 
 * @example
 * const { data, isLoading, error } = usePriceQuery("AAPL");
 * 
 * if (isLoading) return <div>Loading...</div>;
 * if (error) return <div>Error: {error.message}</div>;
 * return <div>Price: ${data.price}</div>;
 */
export const usePriceQuery = (
  symbol: string | undefined,
  options?: {
    refetchInterval?: number; // auto-refresh every N ms
    enabled?: boolean; // manual control
  }
): UseQueryResult<Price, Error> => {
  return useQuery({
    queryKey: ['price', symbol],
    queryFn: () => getCurrentPrice(symbol!),
    enabled: !!symbol && (options?.enabled ?? true),
    staleTime: 60000, // Consider fresh for 1 minute
    refetchInterval: options?.refetchInterval,
    retry: 2,
  });
};
```

**File: `src/api/hooks/useHistoricalQuery.ts`**
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { getHistoricalPrices } from '../endpoints';
import type { HistoricalPrice, HistoricalQueryParams } from '../types';

export const useHistoricalQuery = (
  symbol: string | undefined,
  params: HistoricalQueryParams,
  enabled: boolean = true
): UseQueryResult<HistoricalPrice, Error> => {
  return useQuery({
    queryKey: ['historical', symbol, params],
    queryFn: () => getHistoricalPrices(symbol!, params),
    enabled: !!symbol && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};
```

**File: `src/api/hooks/useConversionQuery.ts`**
```typescript
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { getCurrentConversion, getHistoricalConversion } from '../endpoints';
import type { ConversionResult, HistoricalConversion, HistoricalQueryParams } from '../types';

export const useConversionQuery = (
  asset: string | undefined,
  denomination: string | undefined,
  enabled: boolean = true
): UseQueryResult<ConversionResult, Error> => {
  return useQuery({
    queryKey: ['conversion', asset, denomination],
    queryFn: () => getCurrentConversion(asset!, denomination!),
    enabled: !!asset && !!denomination && enabled,
    staleTime: 60000, // 1 minute
    retry: 2,
  });
};

export const useHistoricalConversionQuery = (
  asset: string | undefined,
  denomination: string | undefined,
  params: HistoricalQueryParams,
  enabled: boolean = true
): UseQueryResult<HistoricalConversion, Error> => {
  return useQuery({
    queryKey: ['historical-conversion', asset, denomination, params],
    queryFn: () => getHistoricalConversion(asset!, denomination!, params),
    enabled: !!asset && !!denomination && enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};
```

**File: `src/api/hooks/useForecastMutation.ts`**
```typescript
import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { generateForecast } from '../endpoints';
import type { ForecastRequest, ForecastResponse } from '../types';

/**
 * Hook for generating forecasts
 * 
 * Uses mutation instead of query because:
 * - Forecasts are expensive (can take 1-10 seconds)
 * - Should only run on explicit user action
 * - Results shouldn't be cached aggressively
 * 
 * @example
 * const forecastMutation = useForecastMutation();
 * 
 * const handleSubmit = () => {
 *   forecastMutation.mutate({
 *     symbol: "AAPL",
 *     horizon_days: 30,
 *     n_paths: 50000
 *   });
 * };
 * 
 * if (forecastMutation.isPending) return <Spinner />;
 * if (forecastMutation.isError) return <Error />;
 * if (forecastMutation.isSuccess) return <Results data={forecastMutation.data} />;
 */
export const useForecastMutation = (): UseMutationResult<
  ForecastResponse,
  Error,
  ForecastRequest
> => {
  return useMutation({
    mutationFn: generateForecast,
    retry: 1, // Only retry once for expensive operations
  });
};
```

---

## Page Specifications

### 1. Home Page / Dashboard

**File: `src/pages/HomePage.tsx`**

**Purpose:** Landing page with overview and quick actions

**Layout:**
```
┌─────────────────────────────────────────┐
│ Header (nav bar)                        │
├─────────────────────────────────────────┤
│                                         │
│  Investment Lab                         │
│  Financial Analysis Platform            │
│                                         │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Prices  │  │ Conversion│  │Forecast││
│  │  View    │  │  Tool     │  │  Tool  ││
│  │  current │  │  Price    │  │  Monte ││
│  │  prices  │  │  assets   │  │  Carlo ││
│  └──────────┘  └──────────┘  └────────┘│
│                                         │
│  Quick Start                            │
│  ┌─────────────────────────────┐       │
│  │ Symbol: [AAPL________]      │       │
│  │ [View Price] [Forecast]     │       │
│  └─────────────────────────────┘       │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
- Hero section with app title/description
- 3 card grid linking to main features
- Quick search bar for immediate symbol lookup
- Simple, clean, welcoming design

**Components to use:**
- `Card` for feature cards
- `Button` for CTAs
- `Input` for quick search
- `Link` from React Router for navigation

---

### 2. Price Viewer Page

**File: `src/pages/PriceViewerPage.tsx`**

**Purpose:** View current and historical prices with denomination switching

**Layout:**
```
┌─────────────────────────────────────────┐
│ Header                                  │
├─────────────────────────────────────────┤
│                                         │
│  ┌────────────────────────────────────┐ │
│  │ Symbol: [AAPL_____] 🔍           │ │
│  │ Denomination: [●USD ○BTC ○GBP ]  │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  AAPL                              │ │
│  │  $175.50  ▲ 2.3%                  │ │
│  │  Apple Inc. • Stock • NASDAQ      │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  Price Chart                       │ │
│  │  [7D][30D][90D][1Y][Custom]       │ │
│  │                                    │ │
│  │      📈 Line chart here            │ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
1. **Symbol search** - Input with validation
2. **Denomination picker** - Radio buttons or tabs (USD/BTC/GBP)
3. **Price card** - Large display of current price with % change
4. **Historical chart** - Line chart with time range selector
5. **Auto-refresh** - Update price every 60 seconds

**State management:**
- Symbol: URL param (`/price?symbol=AAPL`)
- Denomination: URL param (`/price?symbol=AAPL&denom=BTC-USD`)
- Time range: Local state (default 30 days)

**Components:**
- `SymbolSearch` - Input with debounced validation
- `DenominationPicker` - Segmented control
- `PriceCard` - Display price with metadata
- `PriceChart` - Recharts line chart
- `LoadingSpinner` - While fetching
- `ErrorMessage` - If API fails

**API calls:**
1. `usePriceQuery(symbol)` - Current price with auto-refresh
2. `useHistoricalQuery(symbol, { days: 30 })` - Chart data

---

### 3. Conversion Page

**File: `src/pages/ConversionPage.tsx`**

**Purpose:** Compare two assets and view their ratio over time

**Layout:**
```
┌─────────────────────────────────────────┐
│ Header                                  │
├─────────────────────────────────────────┤
│                                         │
│  Asset Conversion                       │
│                                         │
│  ┌───────────────┐  vs  ┌────────────┐ │
│  │ Asset: AAPL   │  →   │ Denom: BTC │ │
│  └───────────────┘      └────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  AAPL / BTC-USD                    │ │
│  │  0.001850 BTC                      │ │
│  │  1 BTC = 540.54 AAPL               │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  Ratio History                     │ │
│  │  [7D][30D][90D][1Y]                │ │
│  │                                    │ │
│  │      📊 Ratio chart                │ │
│  │                                    │ │
│  └────────────────────────────────────┘ │
│                                         │
│  Statistics                            │
│  Min: 0.001650  Max: 0.002100         │
│  Avg: 0.001850  Current: 0.001850     │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
1. **Two symbol inputs** - Asset and Denomination
2. **Current ratio display** - Both directions (A/B and B/A)
3. **Historical ratio chart** - Line chart over time
4. **Summary statistics** - Min/max/avg from API
5. **Swap button** - Quickly flip asset ↔ denomination

**Components:**
- Two `SymbolSearch` components
- `Button` for swap (swap icon from lucide-react)
- `Card` for ratio display
- `RatioChart` - Recharts line chart
- Stats display - Grid of metric cards

**API calls:**
1. `useConversionQuery(asset, denom)` - Current ratio
2. `useHistoricalConversionQuery(asset, denom, { days: 30 })` - Chart data

---

### 4. Forecast Page

**File: `src/pages/ForecastPage.tsx`**

**Purpose:** Generate probabilistic price forecasts using GBM

**Layout:**
```
┌─────────────────────────────────────────┐
│ Header                                  │
├─────────────────────────────────────────┤
│                                         │
│  Price Forecast (Monte Carlo)          │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │ Configuration                      │ │
│  │                                    │ │
│  │ Symbol: [AAPL_____]                │ │
│  │                                    │ │
│  │ Horizon (days): [30____] [slider] │ │
│  │ 1 ──────●──────────────────── 90  │ │
│  │                                    │ │
│  │ Simulation Paths: [10000_]        │ │
│  │ ○ 1k  ○ 10k  ● 50k  ○ 100k       │ │
│  │                                    │ │
│  │ [Generate Forecast]                │ │
│  └────────────────────────────────────┘ │
│                                         │
│  {If loading: spinner}                 │
│  {If error: error message}             │
│                                         │
│  {If success:}                         │
│  ┌────────────────────────────────────┐ │
│  │  AAPL - 30 Day Forecast            │ │
│  │  Current: $175.50                  │ │
│  │  Expected: $178.20 (1.5% gain)     │ │
│  │                                    │ │
│  │  Confidence Intervals              │ │
│  │  ├──●────────────●──┤              │ │
│  │  $158    $178      $200            │ │
│  │  P05     P50       P95             │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  Distribution                      │ │
│  │  📊 Histogram of outcomes          │ │
│  └────────────────────────────────────┘ │
│                                         │
│  ┌────────────────────────────────────┐ │
│  │  Risk Metrics                      │ │
│  │  VaR (95%):  $17.20                │ │
│  │  CVaR (95%): $22.30                │ │
│  │  P(Gain):    52%                   │ │
│  └────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

**Features:**
1. **Configuration form**
   - Symbol input
   - Horizon slider (1-90 days, default 30)
   - Path count radio buttons (1k/10k/50k/100k)
   - Submit button
2. **Loading state** - Spinner while computing (can take 1-10s)
3. **Results display**
   - Summary card (current, expected, probability)
   - Confidence interval visualization
   - Distribution histogram
   - Risk metrics table
4. **Advanced options** (collapsible, optional)
   - Calibration window (default 252 days)
   - Include sample paths (checkbox)

**State management:**
- Form values: Local state with React Hook Form (optional) or useState
- API call: `useForecastMutation()`

**Components:**
- `ForecastForm` - Input form
- `Slider` - For horizon (from shadcn/ui or custom)
- `Radio` buttons - For path count
- `Button` - Submit
- `LoadingSpinner` - During computation
- `ForecastResults` - Summary display
- `ConfidenceIntervals` - Visual bar chart
- `DistributionChart` - Histogram (Recharts)
- `RiskMetrics` - Metrics table

**Flow:**
1. User configures parameters
2. Clicks "Generate Forecast"
3. `useForecastMutation().mutate()` is called
4. Show loading spinner
5. On success: Display results
6. On error: Show error message

---

## Component Specifications

### Layout Components

#### Header Component

**File: `src/components/layout/Header.tsx`**

```typescript
/**
 * Header / Navigation Bar
 * 
 * Fixed at top of page, contains:
 * - Logo/title (left)
 * - Navigation links (center)
 * - Optional user menu (right, for future auth)
 */

// Features:
// - Logo: "Investment Lab" with icon
// - Nav links: Home, Prices, Conversion, Forecast
// - Active link highlighting
// - Mobile responsive (hamburger menu on small screens)

// Styling:
// - Dark background (bg-gray-900)
// - White text
// - Height: 64px
// - Shadow on scroll
// - Sticky position
```

#### Layout Component

**File: `src/components/layout/Layout.tsx`**

```typescript
/**
 * Main layout wrapper
 * 
 * Wraps all pages with consistent structure:
 * - Header at top
 * - Main content area
 * - Optional footer
 * - Responsive padding
 */

// Structure:
<div className="min-h-screen flex flex-col">
  <Header />
  <main className="flex-1 container mx-auto px-4 py-8">
    {children}
  </main>
  {/* Footer optional */}
</div>
```

### Price Components

#### SymbolSearch Component

**File: `src/components/price/SymbolSearch.tsx`**

```typescript
/**
 * Symbol input with validation
 * 
 * Props:
 * - value: string
 * - onChange: (symbol: string) => void
 * - placeholder?: string
 * - error?: string
 * 
 * Features:
 * - Uppercase conversion (AAPL not aapl)
 * - Debounced onChange (300ms)
 * - Error display below input
 * - Search icon
 * - Clear button (X) when value exists
 */

// Validation:
// - Not empty
// - Only alphanumeric + hyphen (BTC-USD)
// - Max 10 characters
```

#### PriceCard Component

**File: `src/components/price/PriceCard.tsx`**

```typescript
/**
 * Display current price with metadata
 * 
 * Props:
 * - price: Price (from API)
 * - denomination?: string (default "USD")
 * 
 * Features:
 * - Large price display
 * - Percentage change (color coded: green up, red down)
 * - Symbol name
 * - Asset type badge
 * - Last updated timestamp
 * - Loading state
 */

// Layout:
// ┌──────────────────────┐
// │ AAPL                 │
// │ $175.50  ▲ 2.3%     │
// │ Apple Inc.           │
// │ Stock • NASDAQ       │
// │ Updated: 2 mins ago  │
// └──────────────────────┘
```

#### DenominationPicker Component

**File: `src/components/price/DenominationPicker.tsx`**

```typescript
/**
 * Select denomination (USD/BTC/GBP)
 * 
 * Props:
 * - value: string (current denomination)
 * - onChange: (denom: string) => void
 * - options?: Array<{label: string, value: string}>
 * 
 * Default options:
 * - USD (US Dollar)
 * - BTC-USD (Bitcoin)
 * - GBP (British Pound)
 * - GLD (Gold ETF)
 * - ETH-USD (Ethereum)
 * 
 * UI:
 * - Segmented control OR dropdown
 * - Icons for each currency (optional)
 * - Active state highlighting
 */
```

### Chart Components

#### PriceChart Component

**File: `src/components/charts/PriceChart.tsx`**

```typescript
/**
 * Historical price line chart
 * 
 * Props:
 * - data: HistoricalPrice (from API)
 * - loading?: boolean
 * - error?: string
 * 
 * Features:
 * - Line chart (Recharts <LineChart>)
 * - X-axis: Time (formatted dates)
 * - Y-axis: Price (auto-scaled)
 * - Tooltip on hover
 * - Responsive
 * - Grid lines
 * - Gradient fill below line (optional)
 * 
 * Time formatters:
 * - 7 days: "Mon", "Tue"
 * - 30 days: "Jan 1", "Jan 15"
 * - 90+ days: "Jan 2025"
 */

// Recharts components:
// <ResponsiveContainer>
//   <LineChart data={...}>
//     <CartesianGrid />
//     <XAxis dataKey="timestamp" />
//     <YAxis />
//     <Tooltip />
//     <Line type="monotone" dataKey="price" />
//   </LineChart>
// </ResponsiveContainer>
```

#### RatioChart Component

**File: `src/components/charts/RatioChart.tsx`**

```typescript
/**
 * Historical ratio line chart
 * 
 * Props:
 * - data: HistoricalConversion (from API)
 * - loading?: boolean
 * 
 * Features:
 * - Same as PriceChart but for ratios
 * - Y-axis label: "Ratio (Asset/Denom)"
 * - Optional: Show both ratio and inverse_ratio as two lines
 * - Color coded (primary color for ratio, secondary for inverse)
 */
```

#### ForecastChart Component

**File: `src/components/charts/ForecastChart.tsx`**

```typescript
/**
 * Forecast visualization with confidence bands
 * 
 * Props:
 * - data: ForecastResponse (from API)
 * 
 * Features:
 * - Sample paths (if available): Multiple thin lines
 * - Mean forecast: Thick line
 * - Confidence bands: Shaded area (P05 to P95)
 * - Current price: Horizontal line
 * - Legend
 * 
 * Implementation:
 * - Use Recharts <AreaChart> for bands
 * - Multiple <Line> components for paths
 * - <ReferenceLine> for current price
 * 
 * Colors:
 * - Sample paths: Light blue, low opacity
 * - Mean: Dark blue
 * - Confidence band: Green, 20% opacity
 * - Current price: Black dashed
 */
```

#### DistributionChart Component

**File: `src/components/charts/DistributionChart.tsx`**

```typescript
/**
 * Histogram of forecast outcomes
 * 
 * Props:
 * - data: ForecastResponse (from API)
 * 
 * Features:
 * - Histogram (bar chart) of terminal price distribution
 * - Vertical lines for current, mean, percentiles
 * - X-axis: Price
 * - Y-axis: Frequency/Probability
 * - Tooltip showing bin range and count
 * 
 * Data processing:
 * - If sample_paths available: Create bins from terminal values
 * - Else: Approximate from percentiles (P05, P25, P50, P75, P95)
 * 
 * Implementation:
 * - <BarChart> from Recharts
 * - <Bar> for histogram
 * - <ReferenceLine> for current/mean/percentiles
 */
```

### Forecast Components

#### ForecastForm Component

**File: `src/components/forecast/ForecastForm.tsx`**

```typescript
/**
 * Form for configuring forecast parameters
 * 
 * Props:
 * - onSubmit: (config: ForecastRequest) => void
 * - loading?: boolean (disable form while computing)
 * 
 * Fields:
 * 1. Symbol input (SymbolSearch component)
 * 2. Horizon days (slider: 1-90, default 30)
 * 3. Path count (radio: 1k/10k/50k/100k, default 10k)
 * 4. Advanced (collapsible):
 *    - Calibration days (input, default 252)
 *    - Include paths (checkbox, default false)
 * 
 * Validation:
 * - Symbol required
 * - Horizon: 1-90
 * - Paths: 1000-100000
 * 
 * Submit button:
 * - Disabled while loading
 * - Shows spinner if loading
 * - Text: "Generate Forecast"
 */
```

#### ForecastResults Component

**File: `src/components/forecast/ForecastResults.tsx`**

```typescript
/**
 * Display forecast statistics
 * 
 * Props:
 * - data: ForecastResponse
 * 
 * Layout:
 * - Summary card at top
 *   - Current price
 *   - Expected price (mean)
 *   - Expected return (%)
 *   - Probability of gain
 * - Charts below
 *   - ForecastChart (if paths available)
 *   - DistributionChart
 * - Risk metrics at bottom
 *   - ConfidenceIntervals component
 *   - RiskMetrics component
 */
```

#### ConfidenceIntervals Component

**File: `src/components/forecast/ConfidenceIntervals.tsx`**

```typescript
/**
 * Visual display of confidence intervals
 * 
 * Props:
 * - current: number (current price)
 * - percentiles: ForecastResponse['percentiles']
 * 
 * Features:
 * - Horizontal bar showing price range
 * - Markers for P05, P25, P50, P75, P95
 * - Current price reference
 * - Labels showing values
 * 
 * Visual:
 * $150        $175        $200
 *  ├────●──────●──────●────┤
 *  P05  P25   P50   P75  P95
 *           ↑
 *       Current: $175
 */
```

#### RiskMetrics Component

**File: `src/components/forecast/RiskMetrics.tsx`**

```typescript
/**
 * Display risk metrics in a table/grid
 * 
 * Props:
 * - data: ForecastResponse
 * 
 * Metrics to show:
 * - VaR (95%): "5% chance of losing more than $X"
 * - CVaR (95%): "Average loss in worst 5% scenarios: $X"
 * - Probability of gain: "X% chance price will be higher"
 * - Expected return: "X% expected return"
 * 
 * Styling:
 * - Grid layout (2x2)
 * - Card for each metric
 * - Icon for each (from lucide-react)
 * - Tooltip with explanation
 */
```

### Common/Shared Components

#### Button Component

**File: `src/components/common/Button.tsx`**

```typescript
/**
 * Reusable button component
 * 
 * Props:
 * - children: ReactNode
 * - onClick?: () => void
 * - variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
 * - size?: 'sm' | 'md' | 'lg'
 * - loading?: boolean
 * - disabled?: boolean
 * - type?: 'button' | 'submit' | 'reset'
 * - className?: string (for extensions)
 * 
 * Features:
 * - Shows spinner when loading
 * - Disabled state styling
 * - Hover/focus states
 * - Variants for different contexts
 */
```

#### Input Component

**File: `src/components/common/Input.tsx`**

```typescript
/**
 * Reusable input component
 * 
 * Props:
 * - value: string
 * - onChange: (value: string) => void
 * - placeholder?: string
 * - error?: string
 * - label?: string
 * - type?: 'text' | 'number' | 'email'
 * - disabled?: boolean
 * - icon?: ReactNode (left icon)
 * - className?: string
 * 
 * Features:
 * - Label above input (optional)
 * - Error message below (red text)
 * - Focus ring
 * - Icon support (search, etc.)
 */
```

#### Card Component

**File: `src/components/common/Card.tsx`**

```typescript
/**
 * Container component for grouping content
 * 
 * Props:
 * - children: ReactNode
 * - title?: string (header)
 * - footer?: ReactNode (optional footer)
 * - className?: string
 * 
 * Styling:
 * - White background
 * - Rounded corners
 * - Shadow
 * - Padding
 * - Optional title bar
 */
```

#### LoadingSpinner Component

**File: `src/components/common/LoadingSpinner.tsx`**

```typescript
/**
 * Loading indicator
 * 
 * Props:
 * - size?: 'sm' | 'md' | 'lg'
 * - message?: string (optional text)
 * 
 * Implementation:
 * - Animated spinner (CSS or Tailwind animation)
 * - Centered by default
 * - Optional message below spinner
 */
```

#### ErrorMessage Component

**File: `src/components/common/ErrorMessage.tsx`**

```typescript
/**
 * Error display component
 * 
 * Props:
 * - error: Error | string
 * - title?: string (default: "Error")
 * - onRetry?: () => void (optional retry button)
 * 
 * Features:
 * - Red alert box
 * - Error icon
 * - Error message
 * - Optional retry button
 */
```

---

## Utility Functions

### Formatters

**File: `src/utils/formatters.ts`**

```typescript
/**
 * Number and date formatting utilities
 */

/**
 * Format price with currency symbol
 * @example formatPrice(175.50, "USD") => "$175.50"
 * @example formatPrice(0.00185, "BTC") => "₿0.00185"
 */
export const formatPrice = (price: number, currency: string): string => {
  const symbols: Record<string, string> = {
    USD: '$',
    GBP: '£',
    EUR: '€',
    BTC: '₿',
  };
  
  const symbol = symbols[currency] || currency;
  const decimals = price < 1 ? 6 : 2; // More decimals for small values
  
  return `${symbol}${price.toFixed(decimals)}`;
};

/**
 * Format percentage change with color
 * @example formatPercentChange(2.5) => { text: "+2.5%", color: "green" }
 */
export const formatPercentChange = (change: number) => {
  const sign = change >= 0 ? '+' : '';
  const color = change >= 0 ? 'text-green-600' : 'text-red-600';
  return {
    text: `${sign}${change.toFixed(2)}%`,
    color,
  };
};

/**
 * Format timestamp for display
 * @example formatTimestamp(date, "short") => "2 mins ago"
 * @example formatTimestamp(date, "long") => "Nov 8, 2025 3:45 PM"
 */
export const formatTimestamp = (
  timestamp: string | Date,
  format: 'short' | 'long' = 'short'
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
  
  // Long format
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

/**
 * Format large numbers with K/M/B suffixes
 * @example formatLargeNumber(1500) => "1.5K"
 * @example formatLargeNumber(2500000) => "2.5M"
 */
export const formatLargeNumber = (num: number): string => {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toString();
};
```

### Validators

**File: `src/utils/validators.ts`**

```typescript
/**
 * Input validation utilities
 */

/**
 * Validate symbol format
 * @example validateSymbol("AAPL") => { valid: true }
 * @example validateSymbol("AAP L") => { valid: false, error: "Invalid characters" }
 */
export const validateSymbol = (symbol: string): { valid: boolean; error?: string } => {
  if (!symbol || symbol.trim().length === 0) {
    return { valid: false, error: 'Symbol is required' };
  }
  
  if (symbol.length > 10) {
    return { valid: false, error: 'Symbol too long (max 10 characters)' };
  }
  
  // Allow alphanumeric and hyphen (for BTC-USD)
  if (!/^[A-Z0-9-]+$/.test(symbol.toUpperCase())) {
    return { valid: false, error: 'Invalid characters (use A-Z, 0-9, -)' };
  }
  
  return { valid: true };
};

/**
 * Validate date range
 */
export const validateDateRange = (
  startDate?: string,
  endDate?: string
): { valid: boolean; error?: string } => {
  if (!startDate || !endDate) {
    return { valid: true }; // Optional parameters
  }
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  if (isNaN(start.getTime())) {
    return { valid: false, error: 'Invalid start date' };
  }
  
  if (isNaN(end.getTime())) {
    return { valid: false, error: 'Invalid end date' };
  }
  
  if (start > end) {
    return { valid: false, error: 'Start date must be before end date' };
  }
  
  const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
  if (diffDays > 365) {
    return { valid: false, error: 'Date range too large (max 365 days)' };
  }
  
  return { valid: true };
};
```

### Constants

**File: `src/utils/constants.ts`**

```typescript
/**
 * Application constants
 */

export const DENOMINATIONS = [
  { label: 'US Dollar', value: 'USD', symbol: '$' },
  { label: 'Bitcoin', value: 'BTC-USD', symbol: '₿' },
  { label: 'British Pound', value: 'GBP', symbol: '£' },
  { label: 'Gold', value: 'GLD', symbol: '🏅' },
  { label: 'Ethereum', value: 'ETH-USD', symbol: 'Ξ' },
] as const;

export const TIME_RANGES = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
  { label: '1Y', days: 365 },
] as const;

export const PATH_COUNTS = [
  { label: '1K', value: 1000 },
  { label: '10K', value: 10000 },
  { label: '50K', value: 50000 },
  { label: '100K', value: 100000 },
] as const;

export const DEFAULT_FORECAST_CONFIG = {
  horizon_days: 30,
  n_paths: 10000,
  calibration_days: 252,
  include_paths: false,
  n_sample_paths: 100,
} as const;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const REFRESH_INTERVALS = {
  PRICE: 60000, // 1 minute
  HISTORICAL: 5 * 60000, // 5 minutes
} as const;
```

---

## Styling Guidelines

### Tailwind Configuration

**File: `tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        success: {
          500: '#10b981',
          600: '#059669',
        },
        danger: {
          500: '#ef4444',
          600: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
```

### Color Scheme

**Primary colors:**
- **Primary:** Blue (#0ea5e9) - buttons, links, active states
- **Success:** Green (#10b981) - positive changes, gains
- **Danger:** Red (#ef4444) - errors, losses
- **Gray:** Neutral grays for text, borders, backgrounds

**Usage:**
- Background: `bg-gray-50` (light gray)
- Cards: `bg-white` with `shadow-md`
- Text: `text-gray-900` (primary), `text-gray-600` (secondary)
- Borders: `border-gray-200`

### Typography

**Font:** Inter (Google Fonts)

**Sizes:**
- Headings: `text-3xl`, `text-2xl`, `text-xl`, `text-lg`
- Body: `text-base`
- Small: `text-sm`
- Extra small: `text-xs`

**Weights:**
- Bold: `font-bold` (headings, emphasis)
- Semibold: `font-semibold` (subheadings)
- Normal: `font-normal` (body text)

### Spacing

**Consistent spacing scale:**
- xs: `p-2` / `m-2` (8px)
- sm: `p-4` / `m-4` (16px)
- md: `p-6` / `m-6` (24px)
- lg: `p-8` / `m-8` (32px)
- xl: `p-12` / `m-12` (48px)

**Container:**
- Use `container mx-auto px-4` for page content
- Max width: `max-w-7xl` for very wide content
- Max width: `max-w-4xl` for reading content

### Responsive Design

**Breakpoints:**
- Mobile: Default (< 640px)
- Tablet: `sm:` (≥ 640px)
- Desktop: `md:` (≥ 768px)
- Large: `lg:` (≥ 1024px)

**Mobile-first approach:**
```tsx
// Stack on mobile, side-by-side on desktop
<div className="flex flex-col md:flex-row gap-4">
  <div>Column 1</div>
  <div>Column 2</div>
</div>
```

---

## State Management

### Global State (Optional)

For simple global state (current symbol, denomination), use React Context.

**File: `src/context/SymbolContext.tsx`**

```typescript
import { createContext, useContext, useState, ReactNode } from 'react';

interface SymbolContextType {
  symbol: string | undefined;
  setSymbol: (symbol: string) => void;
}

const SymbolContext = createContext<SymbolContextType | undefined>(undefined);

export const SymbolProvider = ({ children }: { children: ReactNode }) => {
  const [symbol, setSymbol] = useState<string>();
  
  return (
    <SymbolContext.Provider value={{ symbol, setSymbol }}>
      {children}
    </SymbolContext.Provider>
  );
};

export const useSymbol = () => {
  const context = useContext(SymbolContext);
  if (!context) {
    throw new Error('useSymbol must be used within SymbolProvider');
  }
  return context;
};
```

**Alternative:** Use URL params for symbol/denomination (recommended for shareability)

```typescript
// In component
const [searchParams, setSearchParams] = useSearchParams();
const symbol = searchParams.get('symbol');
const setSymbol = (s: string) => setSearchParams({ symbol: s });
```

---

## Routing

**Use React Router v6**

**File: `src/App.tsx`**

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/HomePage';
import PriceViewerPage from './pages/PriceViewerPage';
import ConversionPage from './pages/ConversionPage';
import ForecastPage from './pages/ForecastPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="price" element={<PriceViewerPage />} />
          <Route path="convert" element={<ConversionPage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

**Navigation:**
```typescript
import { Link, useNavigate } from 'react-router-dom';

// Using Link
<Link to="/price?symbol=AAPL">View AAPL</Link>

// Using navigate programmatically
const navigate = useNavigate();
navigate('/forecast?symbol=AAPL');
```

---

## Setup Instructions

### Initial Setup

```bash
# Create project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install

# Install additional packages
npm install react-router-dom
npm install @tanstack/react-query
npm install axios
npm install recharts
npm install lucide-react

# Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Install dev dependencies
npm install -D @types/node
npm install -D prettier eslint
```

### Configuration Files

**`.env.development`**
```bash
VITE_API_BASE_URL=http://localhost:8000
```

**`src/index.css`**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

body {
  font-family: 'Inter', sans-serif;
}
```

**`src/main.tsx`**
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.tsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
```

---

## Testing Strategy

### Manual Testing Checklist

**Price Viewer:**
- [ ] Search for valid symbol (AAPL) shows price
- [ ] Search for invalid symbol shows error
- [ ] Switch denomination updates display
- [ ] Historical chart loads and displays
- [ ] Time range buttons change chart
- [ ] Auto-refresh updates price every 60s

**Conversion:**
- [ ] Two symbols show ratio
- [ ] Swap button flips asset ↔ denomination
- [ ] Historical chart displays correctly
- [ ] Summary stats match expectations

**Forecast:**
- [ ] Form validation works (required fields)
- [ ] Generate button triggers API call
- [ ] Loading spinner shows during computation
- [ ] Results display all metrics
- [ ] Distribution chart renders
- [ ] Error handling works (invalid symbol)

**General:**
- [ ] Navigation between pages works
- [ ] Mobile responsive (test at 375px width)
- [ ] Error messages display properly
- [ ] Loading states show appropriately
- [ ] CORS works (no browser errors)

### Unit Testing (Optional, for later)

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

Test files: `*.test.tsx` next to components

---

## Development Workflow

### Step 1: Setup (Day 1)
1. Initialize Vite project
2. Install dependencies
3. Configure Tailwind
4. Setup API client
5. Create type definitions
6. Test API connection

### Step 2: Core Components (Day 2)
1. Layout (Header, Layout wrapper)
2. Common components (Button, Input, Card, LoadingSpinner, ErrorMessage)
3. Test with simple placeholder pages

### Step 3: Price Viewer (Day 3)
1. SymbolSearch component
2. DenominationPicker component
3. PriceCard component
4. PriceChart component
5. PriceViewerPage assembly
6. Test end-to-end

### Step 4: Conversion (Day 4)
1. Reuse SymbolSearch for asset & denomination
2. RatioChart component
3. ConversionPage assembly
4. Test conversions

### Step 5: Forecast (Day 5-6)
1. ForecastForm component
2. ForecastChart component
3. DistributionChart component
4. ConfidenceIntervals component
5. RiskMetrics component
6. ForecastResults component
7. ForecastPage assembly
8. Test forecasts with various parameters

### Step 6: Polish (Day 7)
1. HomePage with links
2. Mobile responsive testing
3. Error handling review
4. Loading states review
5. Documentation (README)
6. Clean up console logs

---

## Common Pitfalls & Solutions

### Issue: CORS Errors

**Problem:** Browser blocks API requests

**Solution:** Backend already has CORS configured. If issues persist:
1. Check API is running at `http://localhost:8000`
2. Verify `.env.development` has correct URL
3. Check browser console for specific error

### Issue: API Types Don't Match

**Problem:** TypeScript errors on API responses

**Solution:**
1. Compare `src/api/types.ts` with backend Pydantic models
2. Test API in `/docs` to see actual response
3. Add `console.log()` to see response structure
4. Update types to match

### Issue: Charts Not Rendering

**Problem:** Recharts shows blank

**Solution:**
1. Check data structure matches expected format
2. Ensure `ResponsiveContainer` has defined height
3. Verify data is not empty/undefined
4. Check console for Recharts errors

### Issue: React Query Not Fetching

**Problem:** `useQuery` returns undefined

**Solution:**
1. Check `queryKey` is correct
2. Verify `enabled` option is true
3. Check network tab for actual request
4. Add `onError` to log errors

---

## Performance Optimization

### Code Splitting

```typescript
// Lazy load pages
import { lazy, Suspense } from 'react';

const ForecastPage = lazy(() => import('./pages/ForecastPage'));

// In routes
<Route
  path="forecast"
  element={
    <Suspense fallback={<LoadingSpinner />}>
      <ForecastPage />
    </Suspense>
  }
/>
```

### Memoization

```typescript
// Memoize expensive computations
import { useMemo } from 'react';

const chartData = useMemo(() => {
  return processDataForChart(rawData);
}, [rawData]);

// Memoize components that don't change often
import { memo } from 'react';

const PriceCard = memo(({ price }: { price: Price }) => {
  // Component implementation
});
```

### Debouncing

```typescript
// Debounce symbol search
import { useCallback } from 'react';
import { debounce } from 'lodash'; // or implement custom

const debouncedSearch = useCallback(
  debounce((value: string) => {
    // Perform search
  }, 300),
  []
);
```

---

## Deployment Preparation

### Build for Production

```bash
npm run build
```

Creates optimized production build in `dist/`

### Environment Variables

**`.env.production`**
```bash
VITE_API_BASE_URL=https://api.investment-lab.com
```

### Docker (for later)

**`Dockerfile`**
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Success Criteria

Frontend is complete when:

1. ✅ All 4 pages implemented and functional
2. ✅ All API endpoints successfully called
3. ✅ Charts render correctly with real data
4. ✅ Error handling works (invalid symbols, API errors)
5. ✅ Loading states display appropriately
6. ✅ Mobile responsive (works at 375px width)
7. ✅ No console errors or warnings
8. ✅ TypeScript compiles without errors
9. ✅ Can perform complete workflows:
   - Search symbol → view price → see chart
   - Compare two assets → view ratio history
   - Generate forecast → view results → see distribution
10. ✅ Code is clean, commented, and organized

---

## Additional Resources

**Documentation:**
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [TanStack Query](https://tanstack.com/query/latest/docs/react/overview)
- [Recharts](https://recharts.org/en-US/)
- [React Router](https://reactrouter.com/en/main)

**Backend API:**
- Interactive docs: `http://localhost:8000/docs`
- All endpoints tested and working
- Refer to PROGRESS.md for API details

---

## Notes for Claude Code

**Implementation approach:**
1. Start with setup and configuration
2. Build incrementally (components → pages)
3. Test each component in isolation before integration
4. Follow TypeScript strict mode (no `any` types)
5. Keep components small and focused
6. Extract reusable logic to custom hooks
7. Comment complex logic
8. Use semantic HTML
9. Ensure accessibility (ARIA labels, keyboard navigation)
10. Follow React best practices (keys in lists, proper state management)

**When in doubt:**
- Prefer simplicity over complexity
- Use existing patterns from this spec
- Log errors to console for debugging
- Test in browser frequently
- Check backend API docs at `/docs`

**Communication:**
- Ask clarifying questions if spec is ambiguous
- Suggest improvements if you see issues
- Document any deviations from spec
- Report completion of milestones

---

*This specification is comprehensive and should provide all information needed to implement a fully functional frontend. Good luck!*

**Version:** 1.0  
**Date:** 2025-11-20  
**Status:** Ready for Implementation
