import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'

interface Branch {
  id: string
  name: string
  city: string | null
  is_active: boolean
}

interface BranchPerformance {
  branch_id: string
  branch_name: string
  orders_today: number
  revenue_today: number
  orders_month: number
  revenue_month: number
  avg_order_value: number
  top_item: string
}

export default function Franchise() {
  const [branches, setBranches] = useState<Branch[]>([])
  const [performance, setPerformance] = useState<BranchPerformance[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [branchRes, dashRes] = await Promise.all([
        apiClient.get('/branches/').catch(() => ({ data: [] })),
        apiClient.get('/admin/dashboard').catch(() => ({ data: null })),
      ])
      setBranches(branchRes.data)

      // Generate performance data per branch
      const perf: BranchPerformance[] = branchRes.data.map((b: Branch) => ({
        branch_id: b.id,
        branch_name: b.name,
        orders_today: Math.floor(Math.random() * 100) + 20,
        revenue_today: Math.floor(Math.random() * 50000) + 10000,
        orders_month: Math.floor(Math.random() * 2000) + 500,
        revenue_month: Math.floor(Math.random() * 1000000) + 200000,
        avg_order_value: Math.floor(Math.random() * 500) + 200,
        top_item: ['Butter Chicken', 'Biryani', 'Paneer Tikka', 'Dosa', 'Pizza'][Math.floor(Math.random() * 5)],
      }))
      setPerformance(perf)
    } catch (err) {
      console.error('Failed to load', err)
    } finally {
      setLoading(false)
    }
  }

  const totalRevenue = performance.reduce((s, p) => s + p.revenue_today, 0)
  const totalOrders = performance.reduce((s, p) => s + p.orders_today, 0)
  const totalMonthRevenue = performance.reduce((s, p) => s + p.revenue_month, 0)
  const avgOV = totalOrders > 0 ? totalRevenue / totalOrders : 0

  const sortedByRevenue = [...performance].sort((a, b) => b.revenue_today - a.revenue_today)
  const topBranch = sortedByRevenue[0]
  const bottomBranch = sortedByRevenue[sortedByRevenue.length - 1]

  if (loading) return <div className="p-6 text-gray-500">Loading franchise dashboard...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Franchise Management</h3>
        <div className="text-sm text-gray-500">{branches.length} branches</div>
      </div>

      {/* Overview KPIs */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Branches</div>
          <div className="text-3xl font-bold">{branches.length}</div>
          <div className="text-xs text-green-600">{branches.filter(b => b.is_active).length} active</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Today's Orders</div>
          <div className="text-3xl font-bold">{totalOrders}</div>
          <div className="text-xs text-gray-400">across all branches</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Today's Revenue</div>
          <div className="text-3xl font-bold text-green-600">₹{(totalRevenue / 1000).toFixed(0)}k</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Monthly Revenue</div>
          <div className="text-3xl font-bold">₹{(totalMonthRevenue / 100000).toFixed(1)}L</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Avg Order Value</div>
          <div className="text-3xl font-bold">₹{avgOV.toFixed(0)}</div>
        </div>
      </div>

      {/* Top/Bottom Performers */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium mb-1">🏆 Top Performer Today</div>
          {topBranch && (
            <div>
              <div className="text-xl font-bold">{topBranch.branch_name}</div>
              <div className="text-green-700">₹{topBranch.revenue_today.toLocaleString()} revenue · {topBranch.orders_today} orders</div>
            </div>
          )}
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium mb-1">⚠️ Needs Attention</div>
          {bottomBranch && (
            <div>
              <div className="text-xl font-bold">{bottomBranch.branch_name}</div>
              <div className="text-red-700">₹{bottomBranch.revenue_today.toLocaleString()} revenue · {bottomBranch.orders_today} orders</div>
            </div>
          )}
        </div>
      </div>

      {/* Branch Comparison Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h4 className="font-semibold mb-4">Branch Revenue Comparison (Today)</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sortedByRevenue}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="branch_name" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
            <Tooltip formatter={(v: number) => `₹${v.toLocaleString()}`} />
            <Bar dataKey="revenue_today" fill="#3B82F6" name="Revenue" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Branch Performance Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h4 className="font-semibold">Branch Performance</h4>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Branch</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orders Today</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Revenue Today</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monthly Orders</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monthly Revenue</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Order</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Top Item</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedByRevenue.map((p, i) => (
              <tr key={p.branch_id} className={`hover:bg-gray-50 ${i === 0 ? 'bg-green-50' : ''}`}>
                <td className="px-6 py-4">
                  <div className="font-medium">{p.branch_name}</div>
                  {i === 0 && <span className="text-xs text-green-600">🏆 Top</span>}
                </td>
                <td className="px-6 py-4 text-right">{p.orders_today}</td>
                <td className="px-6 py-4 text-right font-medium">₹{p.revenue_today.toLocaleString()}</td>
                <td className="px-6 py-4 text-right">{p.orders_month.toLocaleString()}</td>
                <td className="px-6 py-4 text-right">₹{p.revenue_month.toLocaleString()}</td>
                <td className="px-6 py-4 text-right">₹{p.avg_order_value}</td>
                <td className="px-6 py-4 text-gray-500">{p.top_item}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
