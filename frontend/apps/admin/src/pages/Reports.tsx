import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

export default function Reports() {
  const [dailySales, setDailySales] = useState<any>(null)
  const [itemSales, setItemSales] = useState<any[]>([])
  const [hourlySales, setHourlySales] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadReports() }, [])

  const loadReports = async () => {
    try {
      const [dailyRes, itemRes, hourlyRes] = await Promise.all([
        apiClient.get('/reports/daily-sales'),
        apiClient.get('/reports/item-wise-sales'),
        apiClient.get('/reports/hourly-sales').catch(() => ({ data: [] })),
      ])
      setDailySales(dailyRes.data)
      setItemSales(itemRes.data)
      setHourlySales(hourlyRes.data)
    } catch (err) {
      console.error('Failed to load reports', err)
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = () => {
    if (!itemSales.length) return
    const headers = 'Item Name,Revenue,Quantity\n'
    const rows = itemSales.map(i => `${i.item_name},${i.total_revenue},${i.total_quantity}`).join('\n')
    const blob = new Blob([headers + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sales-report-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16']

  if (loading) return <div className="text-center py-8 text-gray-500">Loading reports...</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Reports</h3>
        <button onClick={exportCSV} className="bg-gray-100 text-gray-700 px-4 py-2 rounded hover:bg-gray-200 text-sm">
          Export CSV
        </button>
      </div>

      {/* Daily Sales Stats */}
      {dailySales && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold mb-4">Today's Sales</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-600">Orders</p>
              <p className="text-3xl font-bold text-blue-700">{dailySales.order_count}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-600">Revenue</p>
              <p className="text-3xl font-bold text-green-700">₹{Number(dailySales.total_sales).toLocaleString()}</p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="text-sm text-purple-600">Avg Order</p>
              <p className="text-3xl font-bold text-purple-700">₹{Number(dailySales.avg_order_value).toFixed(0)}</p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <p className="text-sm text-orange-600">Tax Collected</p>
              <p className="text-3xl font-bold text-orange-700">₹{Number(dailySales.total_tax).toFixed(0)}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Items Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold mb-4">Top Selling Items</h4>
          {itemSales.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={itemSales.slice(0, 8)} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={v => `₹${v}`} />
                <YAxis type="category" dataKey="item_name" width={80} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => `₹${v.toFixed(0)}`} />
                <Bar dataKey="total_revenue" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No sales data yet</p>
          )}
        </div>

        {/* Payment Methods Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold mb-4">Payment Methods</h4>
          {dailySales?.payment_breakdown?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dailySales.payment_breakdown}
                  dataKey="total"
                  nameKey="method"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ method, percent }) => `${method} ${(percent * 100).toFixed(0)}%`}
                >
                  {dailySales.payment_breakdown.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => `₹${v.toFixed(0)}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-8">No payment data yet</p>
          )}
        </div>
      </div>

      {/* Hourly Sales Chart */}
      {hourlySales.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-md font-semibold mb-4">Hourly Sales</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={hourlySales}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="orders" fill="#10B981" name="Orders" />
              <Bar dataKey="revenue" fill="#3B82F6" name="Revenue (₹)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Item Sales Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h4 className="text-md font-semibold">Item-wise Sales</h4>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Revenue</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty Sold</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {itemSales.map((item, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-6 py-3 text-gray-400">{i + 1}</td>
                <td className="px-6 py-3 font-medium">{item.item_name}</td>
                <td className="px-6 py-3 text-right">₹{Number(item.total_revenue).toFixed(0)}</td>
                <td className="px-6 py-3 text-right">{Number(item.total_quantity)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
