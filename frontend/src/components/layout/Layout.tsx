import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function Layout() {
  return (
    <div className="min-h-screen bg-dark-900">
      <Sidebar />

      {/* Main content area with left margin for sidebar */}
      <main className="ml-64 min-h-screen transition-all duration-300">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
