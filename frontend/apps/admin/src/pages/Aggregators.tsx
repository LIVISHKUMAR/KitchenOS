import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface AggregatorOrder {
  id: string
  order_number: string
  aggregator: string
  aggregator_order_id: string
  status: string
  total: number
  customer_name: string | null
  created_at: string | null
}

const AGGREGATORS = [
  { id: 'swiggy', name: 'Swiggy', color: 'bg-orange-100 text-orange-700', icon: '🟠' },
  { id: 'zomato', name: 'Zomato', color: 'bg-red-100 text-red-700', icon: '🔴' },
  { id: 'uber_eats', name: 'Uber Eats', color: 'bg-green-100 text-green-700', icon: '🟢' },
]

const STATUS_FLOW = ['confirmed', 'preparing', 'ready', 'picked_up', 'delivered']

export default function Aggregators() {
  const [orders, setOrders] = useState<AggregatorOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [filterAggregator, setFilterAggregator] = useState<string>('')
  const [filterStatus, setFilterStatus] = useState<string>('')

  useEffect(() => { loadOrders() }, [filterAggregator, filterStatus])

  const loadOrders = async () => {
    try {
      const params: Record<string, string> = {}
      if (filterAggregator) params.aggregator = filterAggregator
      if (filterStatus) params.status = filterStatus
      const res = await apiClient.get('/aggregator/orders', { params })
      setOrders(res.data)
    } catch (err) {
      console.error('Failed to load aggregator orders', err)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (orderId: string, newStatus: string) => {
    try {
      await apiClient.post(`/aggregator/order/${orderId}/status`, { status: newStatus })
      loadOrders()
    } catch (err: any) {
      console.error('Failed to update status', err)
    }
  }

  const getNextStatus = (current: string) => {
    const idx = STATUS_FLOW.indexOf(current)
    return idx >= 0 && idx < STATUS_FLOW.length - 1 ? STATUS_FLOW[idx + 1] : null
  }

  const statusColors: Record<string, string> = {
    confirmed: 'bg-blue-100 text-blue-700',
    preparing: 'bg-yellow-100 text-yellow-700',
    ready: 'bg-green-100 text-green-700',
    picked_up: 'bg-purple-100 text-purple-700',
    delivered: 'bg-gray-100 text-gray-700',
    cancelled: 'bg-red-100 text-red-700',
  }

  const getAggregatorInfo = (source: string) => AGGREGATORS.find(a => a.id === source) || { name: source, color: 'bg-gray-100 text-gray-700', icon: '🔵' }

  if (loading) return <div className="p-6 text-gray-500">Loading aggregator orders...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Aggregator Orders</h3>
        <div className="flex gap-2">
          <select value={filterAggregator} onChange={e => setFilterAggregator(e.target.value)} className="px-3 py-2 border rounded text-sm">
            <option value="">All Aggregators</option>
            {AGGREGATORS.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="px-3 py-2 border rounded text-sm">
            <option value="">All Status</option>
            {STATUS_FLOW.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {AGGREGATORS.map(agg => {
          const count = orders.filter(o => o.aggregator === agg.id).length
          const revenue = orders.filter(o => o.aggregator === agg.id).reduce((s, o) => s + o.total, 0)
          return (
            <div key={agg.id} className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{agg.icon}</span>
                <span className="font-semibold">{agg.name}</span>
              </div>
              <div className="text-2xl font-bold">{count}</div>
              <div className="text-sm text-gray-500">₹{revenue.toFixed(0)} revenue</div>
            </div>
          )
        })}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">📊</span>
            <span className="font-semibold">Total</span>
          </div>
          <div className="text-2xl font-bold">{orders.length}</div>
          <div className="text-sm text-gray-500">₹{orders.reduce((s, o) => s + o.total, 0).toFixed(0)} revenue</div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aggregator</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {orders.length === 0 ? (
              <tr><td colSpan={7} className="px-6 py-4 text-center text-gray-500">No aggregator orders</td></tr>
            ) : orders.map(order => {
              const agg = getAggregatorInfo(order.aggregator)
              const nextStatus = getNextStatus(order.status)
              return (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium">{order.order_number}</div>
                    <div className="text-xs text-gray-400">{order.aggregator_order_id}</div>
                  </td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${agg.color}`}>{agg.icon} {agg.name}</span></td>
                  <td className="px-6 py-4">{order.customer_name || 'Walk-in'}</td>
                  <td className="px-6 py-4 text-right font-medium">₹{Number(order.total).toFixed(2)}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[order.status] || ''}`}>{order.status}</span></td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{order.created_at ? new Date(order.created_at).toLocaleTimeString() : '-'}</td>
                  <td className="px-6 py-4 text-right">
                    {nextStatus && (
                      <button
                        onClick={() => updateStatus(order.id, nextStatus)}
                        className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                      >
                        {nextStatus === 'preparing' ? 'Start Preparing' :
                         nextStatus === 'ready' ? 'Mark Ready' :
                         nextStatus === 'picked_up' ? 'Picked Up' :
                         nextStatus === 'delivered' ? 'Delivered' : nextStatus}
                      </button>
                    )}
                    {order.status === 'confirmed' && (
                      <button
                        onClick={() => updateStatus(order.id, 'cancelled')}
                        className="text-red-500 hover:text-red-700 text-sm ml-3"
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Integration Config */}
      <div className="mt-6 grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Swiggy Integration</h4>
          <div className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Partner ID</label><input className="w-full px-3 py-2 border rounded" placeholder="Enter Swiggy Partner ID" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">API Key</label><input type="password" className="w-full px-3 py-2 border rounded" placeholder="Enter API key" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label><div className="px-3 py-2 bg-gray-50 rounded text-sm text-gray-600">/api/v1/aggregator/webhook/order</div></div>
            <button className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 text-sm">Save Swiggy Config</button>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="font-semibold mb-4">Zomato Integration</h4>
          <div className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Partner ID</label><input className="w-full px-3 py-2 border rounded" placeholder="Enter Zomato Partner ID" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">API Key</label><input type="password" className="w-full px-3 py-2 border rounded" placeholder="Enter API key" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label><div className="px-3 py-2 bg-gray-50 rounded text-sm text-gray-600">/api/v1/aggregator/webhook/order</div></div>
            <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 text-sm">Save Zomato Config</button>
          </div>
        </div>
      </div>
    </div>
  )
}
