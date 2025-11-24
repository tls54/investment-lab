import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout';
import DashboardPage from './pages/DashboardPage';
import AssetExplorerPage from './pages/AssetExplorerPage';
import ForecastPage from './pages/ForecastPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="explore" element={<AssetExplorerPage />} />
          <Route path="forecast" element={<ForecastPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
