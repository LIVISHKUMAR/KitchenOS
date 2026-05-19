import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

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
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const res = await apiClient.get('/admin/dashboard')
      setData(res.data)
    } catch (err) {
      console.error('Failed to load dashboard', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading...</div>
  if (!data) return <div className="text-center py-8 text-red-500">Failed to load dashboard</div>

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Today's Orders" value={data.today.orders} icon="📋" />
        <StatCard title="Today's Revenue" value={`₹${data.today.revenue.toLocaleString()}`} icon="💰" />
        <StatCard title="Active Orders" value={data.active_orders} icon="⏳" />
        <StatCard title="Total Customers" value={data.customers} icon="👥" />
      </div>

      {/* Weekly/Monthly */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">This Week</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Orders</span>
              <span className="font-semibold">{data.this_week.orders}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Revenue</span>
              <span className="font-semibold">₹{data.this_week.revenue.toLocaleString()}</span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">This Month</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">Orders</span>
              <span className="font-semibold">{data.this_month.orders}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Revenue</span>
              <span className="font-semibold">₹{data.this_month.revenue.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Branches</h3>
          <p className="text-2xl font-bold">{data.branches}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Users</h3>
          <p className="text-2xl font-bold">{data.users}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm text-gray-500 mb-1">Plan</h3>
          <p className="text-2xl font-bold capitalize">{data.tenant?.subscription_plan}</p>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon }: { title: string; value: string | number; icon: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  )
}
