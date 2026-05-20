import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/orders', label: 'Orders', icon: '📋' },
  { path: '/menu', label: 'Menu', icon: '🍽️' },
  { path: '/floor-plan', label: 'Floor Plan', icon: '🗺️' },
  { path: '/reservations', label: 'Reservations', icon: '📅' },
  { path: '/loyalty', label: 'Loyalty', icon: '⭐' },
  { path: '/gst', label: 'GST Reports', icon: '📑' },
  { path: '/recipes', label: 'Recipes', icon: '🧑‍🍳' },
  { path: '/messaging', label: 'Messaging', icon: '💬' },
  { path: '/aggregators', label: 'Aggregators', icon: '🛵' },
  { path: '/analytics', label: 'Analytics', icon: '📊' },
  { path: '/security', label: 'Security', icon: '🔒' },
  { path: '/franchise', label: 'Franchise', icon: '🏢' },
  { path: '/kitchen', label: 'Kitchen', icon: '🔥' },
  { path: '/report-builder', label: 'Reports', icon: '📋' },
  { path: '/advanced-analytics', label: 'Advanced', icon: '🔬' },
  { path: '/compliance', label: 'Compliance', icon: '📋' },
  { path: '/customers', label: 'Customers', icon: '👥' },
  { path: '/inventory', label: 'Inventory', icon: '📦' },
  { path: '/reports', label: 'Reports', icon: '📈' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col" role="navigation" aria-label="Main navigation">
        <div className="p-4 border-b border-gray-100">
          <h1 className="text-xl font-bold text-blue-600">KitchenOS</h1>
          <p className="text-sm text-gray-500">Admin Dashboard</p>
        </div>
        <nav className="flex-1 overflow-y-auto p-2">
          {navItems.map(item => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                aria-current={isActive ? 'page' : undefined}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg mb-0.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span className="text-base" aria-hidden="true">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto flex flex-col">
        <header className="bg-white border-b border-gray-100 px-6 py-3 flex justify-between items-center sticky top-0 z-10">
          <h2 className="text-lg font-semibold text-gray-900">
            {navItems.find(i => i.path === location.pathname)?.label || 'Dashboard'}
          </h2>
          <button
            onClick={() => {
              localStorage.removeItem('admin_token');
              window.location.reload();
            }}
            className="text-sm text-gray-500 hover:text-red-500 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-50"
            aria-label="Logout from admin"
          >
            Logout
          </button>
        </header>
        <div className="flex-1 p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
