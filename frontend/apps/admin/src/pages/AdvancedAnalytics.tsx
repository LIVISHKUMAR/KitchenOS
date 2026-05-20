import React, { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ZAxis, Cell } from 'recharts'

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const HOURS = Array.from({ length: 14 }, (_, i) => `${i + 9}:00`)

// Generate heatmap data
const heatmapData: Array<{ day: string; hour: string; orders: number }> = []
DAYS.forEach(day => {
  HOURS.forEach(hour => {
    const isLunch = parseInt(hour) >= 12 && parseInt(hour) <= 14
    const isDinner = parseInt(hour) >= 19 && parseInt(hour) <= 21
    const isWeekend = day === 'Sat' || day === 'Sun'
    let orders = Math.floor(Math.random() * 15) + 2
    if (isLunch) orders += 15
    if (isDinner) orders += 20
    if (isWeekend) orders += 10
    heatmapData.push({ day, hour, orders })
  })
})

// Food cost margin data
const marginData = [
  { name: 'Butter Chicken', cost: 120, price: 350, margin: 66, volume: 45 },
  { name: 'Biryani', cost: 80, price: 250, margin: 68, volume: 60 },
  { name: 'Paneer Tikka', cost: 90, price: 280, margin: 68, volume: 35 },
  { name: 'Dosa', cost: 30, price: 120, margin: 75, volume: 80 },
  { name: 'Pizza', cost: 100, price: 300, margin: 67, volume: 40 },
  { name: 'Pasta', cost: 60, price: 220, margin: 73, volume: 30 },
  { name: 'Tandoori', cost: 150, price: 400, margin: 63, volume: 25 },
  { name: 'Dal Makhani', cost: 40, price: 180, margin: 78, volume: 55 },
  { name: 'Naan', cost: 10, price: 40, margin: 75, volume: 100 },
  { name: 'Raita', cost: 15, price: 60, margin: 75, volume: 70 },
]

// Customer lifetime value data
const cltvData = Array.from({ length: 20 }, (_, i) => ({
  orders: Math.floor(Math.random() * 50) + 5,
  totalSpend: Math.floor(Math.random() * 20000) + 1000,
  avgOrder: Math.floor(Math.random() * 500) + 150,
}))

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6']

export default function AdvancedAnalytics() {
  const [tab, setTab] = useState<'heatmap' | 'margins' | 'items' | 'customers'>('heatmap')

  const getHeatmapColor = (orders: number) => {
    if (orders >= 35) return 'bg-red-500'
    if (orders >= 25) return 'bg-orange-400'
    if (orders >= 15) return 'bg-yellow-300'
    if (orders >= 8) return 'bg-green-200'
    return 'bg-gray-100'
  }

  const getHeatmapTextColor = (orders: number) => {
    return orders >= 25 ? 'text-white' : 'text-gray-700'
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Advanced Analytics</h3>
        <div className="flex gap-2">
          {(['heatmap', 'margins', 'items', 'customers'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-sm capitalize ${tab === t ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >{t === 'heatmap' ? 'Order Heatmap' : t === 'margins' ? 'Food Margins' : t === 'items' ? 'Item Profit' : 'Customer LTV'}</button>
          ))}
        </div>
      </div>

      {/* Order Heatmap */}
      {tab === 'heatmap' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Order Volume Heatmap (This Week)</h4>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="px-2 py-2 text-xs text-gray-500"></th>
                  {HOURS.map(h => (
                    <th key={h} className="px-2 py-2 text-xs text-gray-500 text-center">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DAYS.map(day => (
                  <tr key={day}>
                    <td className="px-2 py-2 text-sm font-medium text-gray-600">{day}</td>
                    {HOURS.map(hour => {
                      const cell = heatmapData.find(d => d.day === day && d.hour === hour)
                      const orders = cell?.orders || 0
                      return (
                        <td key={hour} className="px-1 py-1">
                          <div
                            className={`w-12 h-10 rounded flex items-center justify-center text-xs font-medium ${getHeatmapColor(orders)} ${getHeatmapTextColor(orders)}`}
                            title={`${day} ${hour}: ${orders} orders`}
                          >
                            {orders}
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center gap-2 mt-4 justify-center">
            <span className="text-xs text-gray-500">Low</span>
            <div className="w-6 h-4 bg-gray-100 rounded" />
            <div className="w-6 h-4 bg-green-200 rounded" />
            <div className="w-6 h-4 bg-yellow-300 rounded" />
            <div className="w-6 h-4 bg-orange-400 rounded" />
            <div className="w-6 h-4 bg-red-500 rounded" />
            <span className="text-xs text-gray-500">High</span>
          </div>
        </div>
      )}

      {/* Food Cost Margins */}
      {tab === 'margins' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Food Cost vs Selling Price</h4>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={marginData} layout="vertical" margin={{ left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={v => `₹${v}`} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => `₹${v}`} />
                <Bar dataKey="cost" fill="#EF4444" name="Cost" stackId="a" />
                <Bar dataKey="price" fill="#10B981" name="Price" stackId="b" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b">
              <h4 className="font-semibold">Margin Analysis</h4>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Margin</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Volume</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {marginData.sort((a, b) => b.margin - a.margin).map(item => (
                  <tr key={item.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium">{item.name}</td>
                    <td className="px-6 py-4 text-right text-red-600">₹{item.cost}</td>
                    <td className="px-6 py-4 text-right text-green-600">₹{item.price}</td>
                    <td className="px-6 py-4 text-right font-bold">{item.margin}%</td>
                    <td className="px-6 py-4 text-right">{item.volume}/day</td>
                    <td className="px-6 py-4 text-right">
                      {item.margin >= 70 ? (
                        <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Excellent</span>
                      ) : item.margin >= 60 ? (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">Good</span>
                      ) : (
                        <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">Review</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Item Profitability Scatter */}
      {tab === 'items' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Item Profitability (Volume vs Margin)</h4>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ bottom: 20, left: 20 }}>
              <CartesianGrid />
              <XAxis dataKey="volume" name="Volume" label={{ value: 'Daily Volume', position: 'bottom' }} />
              <YAxis dataKey="margin" name="Margin %" label={{ value: 'Margin %', angle: -90, position: 'insideLeft' }} />
              <ZAxis dataKey="price" range={[100, 400]} name="Price" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(v: number, name: string) => name === 'Price' ? `₹${v}` : `${v}%`} />
              <Scatter data={marginData} fill="#3B82F6">
                {marginData.map((entry, i) => (
                  <Cell key={i} fill={entry.margin >= 70 ? '#10B981' : entry.margin >= 60 ? '#F59E0B' : '#EF4444'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-4 justify-center text-sm">
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-500 rounded-full" /> High margin (70%+)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-500 rounded-full" /> Medium (60-70%)</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-500 rounded-full" /> Low (&lt;60%)</span>
          </div>
        </div>
      )}

      {/* Customer Lifetime Value */}
      {tab === 'customers' && (
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Avg Customer LTV</div>
              <div className="text-2xl font-bold">₹{Math.round(cltvData.reduce((s, c) => s + c.totalSpend, 0) / cltvData.length).toLocaleString()}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Avg Orders per Customer</div>
              <div className="text-2xl font-bold">{Math.round(cltvData.reduce((s, c) => s + c.orders, 0) / cltvData.length)}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Avg Order Value</div>
              <div className="text-2xl font-bold">₹{Math.round(cltvData.reduce((s, c) => s + c.avgOrder, 0) / cltvData.length)}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Top Customer Spend</div>
              <div className="text-2xl font-bold text-green-600">₹{Math.max(...cltvData.map(c => c.totalSpend)).toLocaleString()}</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Customer Spend Distribution</h4>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart>
                <CartesianGrid />
                <XAxis dataKey="orders" name="Orders" />
                <YAxis dataKey="totalSpend" name="Total Spend" tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number, name: string) => name === 'Total Spend' ? `₹${v.toLocaleString()}` : v} />
                <Scatter data={cltvData} fill="#8B5CF6" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
