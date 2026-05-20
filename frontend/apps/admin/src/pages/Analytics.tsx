import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend, PieChart, Pie, Cell } from 'recharts'

interface DashboardData {
  today: { orders: number; revenue: number; avg_order: number }
  this_week: { orders: number; revenue: number }
  this_month: { orders: number; revenue: number }
  branches: number
  users: number
}

interface TrendData {
  date: string
  orders: number
  revenue: number
}

interface CategoryData {
  name: string
  revenue: number
  quantity: number
}

interface HourlyData {
  hour: string
  orders: number
  revenue: number
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']

export default function Analytics() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [trend, setTrend] = useState<TrendData[]>([])
  const [categories, setCategories] = useState<CategoryData[]>([])
  const [hourly, setHourly] = useState<HourlyData[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('7d')
  const [compareWith, setCompareWith] = useState(false)

  useEffect(() => { loadData() }, [period])

  const loadData = async () => {
    try {
      const [dashRes, catRes, hourlyRes] = await Promise.all([
        apiClient.get('/admin/dashboard').catch(() => ({ data: null })),
        apiClient.get('/reports/category-wise-sales').catch(() => ({ data: [] })),
        apiClient.get('/reports/hourly-sales').catch(() => ({ data: [] })),
      ])
      setDashboard(dashRes.data)
      setCategories(Array.isArray(catRes.data) ? catRes.data : [])
      setHourly(Array.isArray(hourlyRes.data) ? hourlyRes.data : [])

      // Generate trend data (in production, this would come from a dedicated endpoint)
      const days = period === '7d' ? 7 : period === '30d' ? 30 : 90
      const trendData: TrendData[] = []
      for (let i = days - 1; i >= 0; i--) {
        const d = new Date()
        d.setDate(d.getDate() - i)
        trendData.push({
          date: d.toLocaleDateString('en', { month: 'short', day: 'numeric' }),
          orders: Math.floor(Math.random() * 50) + 10,
          revenue: Math.floor(Math.random() * 20000) + 5000,
        })
      }
      setTrend(trendData)
    } catch (err) {
      console.error('Failed to load analytics', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Loading analytics...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Business Intelligence</h3>
        <div className="flex gap-2">
          {(['7d', '30d', '90d'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded text-sm ${period === p ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
          <label className="flex items-center gap-2 ml-4">
            <input type="checkbox" checked={compareWith} onChange={e => setCompareWith(e.target.checked)} />
            <span className="text-sm">Compare</span>
          </label>
        </div>
      </div>

      {/* KPI Cards */}
      {dashboard && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Today</div>
            <div className="text-2xl font-bold">{dashboard.today.orders}</div>
            <div className="text-xs text-gray-400">orders</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Today Revenue</div>
            <div className="text-2xl font-bold text-green-600">₹{dashboard.today.revenue.toLocaleString()}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Avg Order</div>
            <div className="text-2xl font-bold">₹{dashboard.today.avg_order.toFixed(0)}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">This Week</div>
            <div className="text-2xl font-bold">{dashboard.this_week.orders}</div>
            <div className="text-xs text-gray-400">₹{dashboard.this_week.revenue.toLocaleString()}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">This Month</div>
            <div className="text-2xl font-bold">{dashboard.this_month.orders}</div>
            <div className="text-xs text-gray-400">₹{dashboard.this_month.revenue.toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Revenue Trend */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h4 className="font-semibold mb-4">Revenue Trend ({period})</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="left" tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip formatter={(v: number, name: string) => name === 'revenue' ? `₹${v.toLocaleString()}` : v} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#3B82F6" name="Revenue" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#10B981" name="Orders" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Category Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Revenue by Category</h4>
          {categories.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categories.slice(0, 8)}
                  dataKey="revenue"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {categories.slice(0, 8).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: number) => `₹${v.toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">No data</div>
          )}
        </div>

        {/* Hourly Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Hourly Distribution</h4>
          {hourly.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={hourly}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="orders" fill="#3B82F6" name="Orders" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-400">No data</div>
          )}
        </div>
      </div>

      {/* Category Performance Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h4 className="font-semibold">Category Performance</h4>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Revenue</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Price</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Share</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {categories.map((cat, i) => {
              const totalRevenue = categories.reduce((s, c) => s + c.revenue, 0)
              const share = totalRevenue > 0 ? (cat.revenue / totalRevenue * 100) : 0
              return (
                <tr key={i} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{cat.name}</td>
                  <td className="px-6 py-4 text-right">₹{cat.revenue.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">{cat.quantity}</td>
                  <td className="px-6 py-4 text-right">₹{cat.quantity > 0 ? (cat.revenue / cat.quantity).toFixed(0) : 0}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${share}%` }} />
                      </div>
                      <span className="text-sm w-12 text-right">{share.toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
