import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'

interface PrepMetric {
  item_name: string
  avg_prep_time: number
  target_prep_time: number
  orders_count: number
  sla_compliance: number
}

interface HourlyMetric {
  hour: string
  avg_prep_time: number
  orders: number
}

interface StationMetric {
  station: string
  avg_prep_time: number
  orders: number
  bottleneck_score: number
}

export default function KitchenAnalytics() {
  const [prepMetrics, setPrepMetrics] = useState<PrepMetric[]>([])
  const [hourlyMetrics, setHourlyMetrics] = useState<HourlyMetric[]>([])
  const [stationMetrics, setStationMetrics] = useState<StationMetric[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('today')

  useEffect(() => { loadData() }, [period])

  const loadData = async () => {
    try {
      // In production, these would come from dedicated analytics endpoints
      // For now, generate representative data
      const items = ['Butter Chicken', 'Biryani', 'Paneer Tikka', 'Dosa', 'Pizza', 'Pasta', 'Tandoori', 'Dal Makhani']
      const prep: PrepMetric[] = items.map(name => ({
        item_name: name,
        avg_prep_time: Math.floor(Math.random() * 15) + 8,
        target_prep_time: Math.floor(Math.random() * 5) + 15,
        orders_count: Math.floor(Math.random() * 50) + 10,
        sla_compliance: Math.floor(Math.random() * 30) + 70,
      }))
      setPrepMetrics(prep)

      const hourly: HourlyMetric[] = Array.from({ length: 12 }, (_, i) => ({
        hour: `${i + 11}:00`,
        avg_prep_time: Math.floor(Math.random() * 10) + 10,
        orders: Math.floor(Math.random() * 30) + 5,
      }))
      setHourlyMetrics(hourly)

      const stations: StationMetric[] = [
        { station: 'Tandoor', avg_prep_time: 18, orders: 45, bottleneck_score: 85 },
        { station: 'Grill', avg_prep_time: 15, orders: 38, bottleneck_score: 72 },
        { station: 'Curry', avg_prep_time: 12, orders: 52, bottleneck_score: 65 },
        { station: 'Biryani', avg_prep_time: 25, orders: 30, bottleneck_score: 90 },
        { station: 'Bar', avg_prep_time: 5, orders: 25, bottleneck_score: 30 },
        { station: 'Dessert', avg_prep_time: 8, orders: 20, bottleneck_score: 40 },
      ]
      setStationMetrics(stations)
    } catch (err) {
      console.error('Failed to load', err)
    } finally {
      setLoading(false)
    }
  }

  const overallSLA = prepMetrics.length > 0
    ? Math.round(prepMetrics.reduce((s, m) => s + m.sla_compliance, 0) / prepMetrics.length)
    : 0

  const avgPrepTime = prepMetrics.length > 0
    ? Math.round(prepMetrics.reduce((s, m) => s + m.avg_prep_time, 0) / prepMetrics.length)
    : 0

  const bottleneckStation = stationMetrics.reduce((max, s) => s.bottleneck_score > max.bottleneck_score ? s : max, stationMetrics[0])

  if (loading) return <div className="p-6 text-gray-500">Loading kitchen analytics...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Kitchen Analytics</h3>
        <div className="flex gap-2">
          {(['today', 'week', 'month'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1 rounded text-sm capitalize ${period === p ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
            >{p}</button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Overall SLA</div>
          <div className={`text-3xl font-bold ${overallSLA >= 90 ? 'text-green-600' : overallSLA >= 75 ? 'text-yellow-600' : 'text-red-600'}`}>
            {overallSLA}%
          </div>
          <div className="text-xs text-gray-400">on-time delivery</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Avg Prep Time</div>
          <div className="text-3xl font-bold">{avgPrepTime}m</div>
          <div className="text-xs text-gray-400">across all items</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Bottleneck</div>
          <div className="text-2xl font-bold text-orange-600">{bottleneckStation?.station || '-'}</div>
          <div className="text-xs text-gray-400">score: {bottleneckStation?.bottleneck_score || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Items Tracked</div>
          <div className="text-3xl font-bold">{prepMetrics.length}</div>
          <div className="text-xs text-gray-400">with prep times</div>
        </div>
      </div>

      {/* Hourly Prep Time Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h4 className="font-semibold mb-4">Hourly Prep Time Trend</h4>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={hourlyMetrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis yAxisId="left" label={{ value: 'Minutes', angle: -90, position: 'insideLeft' }} />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="avg_prep_time" stroke="#F59E0B" name="Avg Prep Time (min)" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#3B82F6" name="Orders" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Station Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Station Performance</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stationMetrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="station" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avg_prep_time" fill="#F59E0B" name="Avg Prep (min)" />
              <Bar dataKey="orders" fill="#3B82F6" name="Orders" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Bottleneck Heatmap */}
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Bottleneck Scores</h4>
          <div className="space-y-3">
            {stationMetrics.sort((a, b) => b.bottleneck_score - a.bottleneck_score).map(s => (
              <div key={s.station} className="flex items-center gap-3">
                <span className="w-20 text-sm font-medium">{s.station}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6 relative overflow-hidden">
                  <div
                    className={`h-6 rounded-full flex items-center justify-end pr-2 text-xs font-bold text-white ${
                      s.bottleneck_score >= 80 ? 'bg-red-500' :
                      s.bottleneck_score >= 60 ? 'bg-orange-500' :
                      s.bottleneck_score >= 40 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${s.bottleneck_score}%` }}
                  >
                    {s.bottleneck_score}%
                  </div>
                </div>
                <span className="text-sm text-gray-500 w-16">{s.avg_prep_time}m avg</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Item Prep Time Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h4 className="font-semibold">Item Prep Time Analysis</h4>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Prep</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Target</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orders</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">SLA</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {prepMetrics.sort((a, b) => b.sla_compliance - a.sla_compliance).map(m => (
              <tr key={m.item_name} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium">{m.item_name}</td>
                <td className="px-6 py-4 text-right">{m.avg_prep_time}m</td>
                <td className="px-6 py-4 text-right text-gray-500">{m.target_prep_time}m</td>
                <td className="px-6 py-4 text-right">{m.orders_count}</td>
                <td className="px-6 py-4 text-right">
                  <span className={`font-bold ${
                    m.sla_compliance >= 90 ? 'text-green-600' :
                    m.sla_compliance >= 75 ? 'text-yellow-600' : 'text-red-600'
                  }`}>{m.sla_compliance}%</span>
                </td>
                <td className="px-6 py-4 text-right">
                  {m.sla_compliance >= 90 ? (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">On Track</span>
                  ) : m.sla_compliance >= 75 ? (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">Warning</span>
                  ) : (
                    <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">Needs Attention</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
