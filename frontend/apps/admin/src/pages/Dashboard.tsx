import React from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { StatCardSkeleton } from '../components/Skeleton'

interface DashboardData {
  tenant: { name: string; subscription_plan: string }
  branches: number
  users: number
  customers: number
  active_orders: number
  today: { orders: number; revenue: number }
  this_week: { orders: number; revenue: number }
  this_month: { orders: number; revenue: number }
}

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.dashboard.stats(),
    queryFn: () => apiClient.get('/admin/dashboard').then(res => res.data),
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-500 text-lg">Failed to load dashboard</p>
        <button onClick={() => refetch()} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
          Retry
        </button>
      </div>
    )
  }

  const todayAvg = data.today.orders > 0 ? Math.round(data.today.revenue / data.today.orders) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{data.tenant?.name || 'Dashboard'}</h2>
          <p className="text-sm text-gray-500 mt-1">Real-time overview of your restaurant</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium capitalize">
            {data.tenant?.subscription_plan || 'trial'}
          </span>
          <button onClick={() => refetch()} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors" title="Refresh">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      </div>

      {/* Primary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Today's Orders"
          value={data.today.orders}
          icon="📋"
          color="blue"
        />
        <StatCard
          title="Today's Revenue"
          value={`₹${data.today.revenue.toLocaleString()}`}
          icon="💰"
          color="green"
        />
        <StatCard
          title="Active Orders"
          value={data.active_orders}
          icon="⏳"
          color="orange"
          pulse={data.active_orders > 0}
        />
        <StatCard
          title="Avg Order Value"
          value={`₹${todayAvg.toLocaleString()}`}
          icon="📊"
          color="purple"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-100 p-4">
        <h3 className="text-sm font-semibold text-gray-500 mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <QuickAction icon="📋" label="View Orders" href="/orders" />
          <QuickAction icon="🍽️" label="Manage Menu" href="/menu" />
          <QuickAction icon="📦" label="Inventory" href="/inventory" />
          <QuickAction icon="📈" label="Reports" href="/reports" />
          <QuickAction icon="👥" label="Customers" href="/customers" />
          <QuickAction icon="🗺️" label="Floor Plan" href="/floor-plan" />
        </div>
      </div>

      {/* Weekly & Monthly */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <PeriodCard title="This Week" orders={data.this_week.orders} revenue={data.this_week.revenue} />
        <PeriodCard title="This Month" orders={data.this_month.orders} revenue={data.this_month.revenue} />
      </div>

      {/* Bottom Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MiniStat icon="🏢" label="Branches" value={data.branches} />
        <MiniStat icon="👤" label="Users" value={data.users} />
        <MiniStat icon="❤️" label="Customers" value={data.customers} />
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color, pulse }: {
  title: string; value: string | number; icon: string; color: string; pulse?: boolean
}) {
  const colorStyles: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
  }

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorStyles[color]} flex items-center justify-center text-2xl ${pulse ? 'animate-pulse' : ''}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function QuickAction({ icon, label, href }: { icon: string; label: string; href: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-sm font-medium text-gray-700"
    >
      <span>{icon}</span>
      {label}
    </a>
  )
}

function PeriodCard({ title, orders, revenue }: { title: string; orders: number; revenue: number }) {
  const avg = orders > 0 ? Math.round(revenue / orders) : 0

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-xs text-gray-500">Orders</p>
          <p className="text-xl font-bold text-gray-900">{orders}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Revenue</p>
          <p className="text-xl font-bold text-gray-900">₹{revenue.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Avg Value</p>
          <p className="text-xl font-bold text-gray-900">₹{avg.toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}

function MiniStat({ icon, label, value }: { icon: string; label: string; value: number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 flex items-center gap-4">
      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-xl">{icon}</div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  )
}
