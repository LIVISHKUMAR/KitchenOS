import React, { useEffect, useState, useCallback } from 'react'
import axios from 'axios'

interface KOTItem {
  id: string
  order_id: string
  order_number: string
  item_name: string
  quantity: number
  cooking_instructions: string | null
  course_type: string | null
  prep_status: string
  priority: string
  table_id: string | null
  created_at: string
}

interface KOTOrder {
  order_id: string
  order_number: string
  table_id: string | null
  order_type: string
  items: KOTItem[]
  created_at: string
}

export default function KDSDashboard() {
  const [orders, setOrders] = useState<KOTOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [ws, setWs] = useState<WebSocket | null>(null)

  const loadOrders = useCallback(async () => {
    try {
      const token = localStorage.getItem('kds_token')
      const res = await axios.get('/api/v1/kot/', {
        headers: { Authorization: `Bearer ${token}` },
      })
      setOrders(res.data)
    } catch (err) {
      console.error('Failed to load KOT orders', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadOrders()

    // Poll for updates every 10 seconds
    const interval = setInterval(loadOrders, 10000)
    return () => clearInterval(interval)
  }, [loadOrders])

  const updateItemStatus = async (itemId: string, newStatus: string) => {
    try {
      const token = localStorage.getItem('kds_token')
      await axios.put(`/api/v1/kot/items/${itemId}/status`,
        { prep_status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      loadOrders()
    } catch (err) {
      console.error('Failed to update status', err)
    }
  }

  const getTimeSince = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m`
    return `${Math.floor(mins / 60)}h ${mins % 60}m`
  }

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-500',
    preparing: 'bg-blue-500',
    ready: 'bg-green-500',
  }

  const priorityColors: Record<string, string> = {
    high: 'border-red-500',
    normal: 'border-gray-600',
    low: 'border-gray-700',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading Kitchen Display...</div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 px-6 py-3 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-orange-400">Kitchen Display</h1>
          <span className="text-gray-400">{orders.length} orders</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            {new Date().toLocaleTimeString()}
          </span>
          <button
            onClick={loadOrders}
            className="px-4 py-2 bg-orange-500 rounded hover:bg-orange-600 text-sm"
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Orders Grid */}
      <div className="flex-1 overflow-auto p-4">
        {orders.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500 text-xl">
            No pending orders
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {orders.map(order => (
              <div
                key={order.order_id}
                className={`bg-gray-800 rounded-lg border-l-4 ${priorityColors[order.items[0]?.priority || 'normal']}`}
              >
                {/* Order Header */}
                <div className="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                  <div>
                    <span className="text-lg font-bold text-orange-400">
                      #{order.order_number}
                    </span>
                    {order.table_id && (
                      <span className="ml-2 text-sm text-gray-400">Table</span>
                    )}
                  </div>
                  <span className="text-sm text-gray-400">
                    {getTimeSince(order.created_at)}
                  </span>
                </div>

                {/* Items */}
                <div className="px-4 py-2 space-y-2">
                  {order.items.map(item => (
                    <div
                      key={item.id}
                      className={`flex items-center justify-between py-2 px-3 rounded ${
                        item.prep_status === 'ready' ? 'bg-green-900/30' : ''
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-lg">{item.quantity}x</span>
                          <span className={item.prep_status === 'ready' ? 'line-through text-gray-500' : ''}>
                            {item.item_name}
                          </span>
                        </div>
                        {item.cooking_instructions && (
                          <p className="text-sm text-yellow-400 mt-1">
                            Note: {item.cooking_instructions}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-1">
                        {item.prep_status === 'pending' && (
                          <button
                            onClick={() => updateItemStatus(item.id, 'preparing')}
                            className="px-3 py-1 bg-blue-500 rounded text-sm hover:bg-blue-600"
                          >
                            Start
                          </button>
                        )}
                        {item.prep_status === 'preparing' && (
                          <button
                            onClick={() => updateItemStatus(item.id, 'ready')}
                            className="px-3 py-1 bg-green-500 rounded text-sm hover:bg-green-600"
                          >
                            Ready
                          </button>
                        )}
                        {item.prep_status === 'ready' && (
                          <span className="px-3 py-1 text-green-400 text-sm">Done</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
