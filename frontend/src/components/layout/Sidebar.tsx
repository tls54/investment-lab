import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  LineChart,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  {
    path: '/',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'Overview & quick stats'
  },
  {
    path: '/explore',
    label: 'Asset Explorer',
    icon: LineChart,
    description: 'Prices & conversions'
  },
  {
    path: '/forecast',
    label: 'Forecast',
    icon: TrendingUp,
    description: 'Monte Carlo simulation'
  },
];

export function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-dark-800 border-r border-border
        flex flex-col transition-all duration-300 z-40
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-accent-blue rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-text-primary">Investment Lab</span>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 bg-accent-blue rounded-lg flex items-center justify-center mx-auto">
            <Activity className="w-5 h-5 text-white" />
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200
                ${isActive
                  ? 'bg-accent-blue/10 text-accent-blue'
                  : 'text-text-secondary hover:bg-dark-600 hover:text-text-primary'
                }
                ${collapsed ? 'justify-center' : ''}
              `}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-accent-blue' : ''}`} />
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{item.label}</div>
                  <div className="text-xs text-text-muted truncate">{item.description}</div>
                </div>
              )}
              {isActive && !collapsed && (
                <div className="w-1.5 h-1.5 bg-accent-blue rounded-full" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Settings & Collapse */}
      <div className="p-2 border-t border-border space-y-1">
        <Link
          to="/settings"
          className={`
            flex items-center gap-3 px-3 py-3 rounded-lg text-text-secondary
            hover:bg-dark-600 hover:text-text-primary transition-all duration-200
            ${collapsed ? 'justify-center' : ''}
          `}
          title={collapsed ? 'Settings' : undefined}
        >
          <Settings className="w-5 h-5" />
          {!collapsed && <span className="text-sm font-medium">Settings</span>}
        </Link>

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={`
            w-full flex items-center gap-3 px-3 py-3 rounded-lg text-text-muted
            hover:bg-dark-600 hover:text-text-primary transition-all duration-200
            ${collapsed ? 'justify-center' : ''}
          `}
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
