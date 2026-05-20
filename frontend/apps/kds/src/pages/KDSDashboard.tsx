import React, { useEffect, useState, useCallback, useRef } from 'react'
import axios from 'axios'

interface KOTItem {
  id: string
  order_id: string
  order_number: string
  menu_item_id: string
  item_name: string
  quantity: number
  modifiers: unknown[]
  cooking_instructions: string | null
  course_type: string | null
  prep_status: string
  priority: string
  table_id: string | null
  created_at: string
  prep_started_at?: string | null
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
  const [connected, setConnected] = useState(false)
  const [currentTime, setCurrentTime] = useState(new Date())
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>()
  const audioContextRef = useRef<AudioContext | null>(null)

  // Update clock every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('kds_token') || localStorage.getItem('access_token')
    return { Authorization: `Bearer ${token}` }
  }, [])

  const loadOrders = useCallback(async () => {
    try {
      const res = await axios.get('/api/v1/kot/', { headers: getAuthHeaders() })
      setOrders(res.data)
    } catch (err) {
      console.error('Failed to load KOT orders', err)
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders])

  // Play notification sound
  const playSound = useCallback((type: 'new_order' | 'overdue' | 'ready') => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext()
      }
      const ctx = audioContextRef.current
      const oscillator = ctx.createOscillator()
      const gain = ctx.createGain()

      oscillator.connect(gain)
      gain.connect(ctx.destination)

      if (type === 'new_order') {
        oscillator.frequency.value = 800
        gain.gain.value = 0.3
        oscillator.start()
        oscillator.stop(ctx.currentTime + 0.15)
        setTimeout(() => {
          const osc2 = ctx.createOscillator()
          const gain2 = ctx.createGain()
          osc2.connect(gain2)
          gain2.connect(ctx.destination)
          osc2.frequency.value = 1000
          gain2.gain.value = 0.3
          osc2.start()
          osc2.stop(ctx.currentTime + 0.15)
        }, 200)
      } else if (type === 'overdue') {
        oscillator.frequency.value = 400
        gain.gain.value = 0.4
        oscillator.start()
        oscillator.stop(ctx.currentTime + 0.5)
      }
    } catch {
      // Audio not available
    }
  }, [])

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const token = localStorage.getItem('kds_token') || localStorage.getItem('access_token')
      if (!token) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws?token=${token}&client_type=kds`

      const websocket = new WebSocket(wsUrl)
      wsRef.current = websocket

      websocket.onopen = () => {
        setConnected(true)
        console.log('KDS WebSocket connected')
      }

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          switch (data.type) {
            case 'kot.new':
            case 'order.created':
              playSound('new_order')
              loadOrders()
              break
            case 'kot.updated':
              loadOrders()
              break
            case 'order.updated':
              loadOrders()
              break
            case 'connected':
              break
            case 'pong':
              break
          }
        } catch {
          // Ignore parse errors
        }
      }

      websocket.onclose = () => {
        setConnected(false)
        // Reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(connectWebSocket, 3000)
      }

      websocket.onerror = () => {
        websocket.close()
      }
    }

    connectWebSocket()

    // Fallback polling every 30 seconds if WebSocket fails
    const pollingInterval = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        loadOrders()
      }
    }, 30000)

    // Ping every 25 seconds to keep connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 25000)

    return () => {
      wsRef.current?.close()
      clearInterval(pollingInterval)
      clearInterval(pingInterval)
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
    }
  }, [loadOrders, playSound])

  // Initial load
  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  // Check for overdue items every 10 seconds
  useEffect(() => {
    const checkOverdue = setInterval(() => {
      const now = Date.now()
      for (const order of orders) {
        for (const item of order.items) {
          if (item.prep_status === 'preparing' && item.prep_started_at) {
            const elapsed = now - new Date(item.prep_started_at).getTime()
            // Assume 15 min default prep time
            if (elapsed > 15 * 60 * 1000) {
              playSound('overdue')
              return
            }
          }
        }
      }
    }, 10000)
    return () => clearInterval(checkOverdue)
  }, [orders, playSound])

  const updateItemStatus = async (itemId: string, newStatus: string) => {
    try {
      await axios.put(`/api/v1/kot/items/${itemId}/status`,
        { prep_status: newStatus },
        { headers: getAuthHeaders() }
      )
      // Optimistic update
      setOrders(prev => prev.map(order => ({
        ...order,
        items: order.items.map(item =>
          item.id === itemId ? { ...item, prep_status: newStatus } : item
        )
      })).filter(order => order.items.some(i => i.prep_status !== 'served')))
    } catch (err) {
      console.error('Failed to update status', err)
      loadOrders() // Revert on error
    }
  }

  const getTimeSince = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m`
    return `${Math.floor(mins / 60)}h ${mins % 60}m`
  }

  const getPrepTimer = (item: KOTItem) => {
    if (item.prep_status !== 'preparing' || !item.prep_started_at) return null
    const elapsed = Date.now() - new Date(item.prep_started_at).getTime()
    const mins = Math.floor(elapsed / 60000)
    const secs = Math.floor((elapsed % 60000) / 1000)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const isOverdue = (item: KOTItem) => {
    if (item.prep_status !== 'preparing' || !item.prep_started_at) return false
    const elapsed = Date.now() - new Date(item.prep_started_at).getTime()
    return elapsed > 15 * 60 * 1000 // 15 minutes
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

  const orderTypeIcons: Record<string, string> = {
    dine_in: '🍽️',
    takeaway: '📦',
    delivery: '🚗',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900">
        <div className="text-xl text-white">Loading Kitchen Display...</div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 px-6 py-3 flex justify-between items-center border-b border-gray-700">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-orange-400">KitchenOS KDS</h1>
          <span className="text-gray-400">{orders.length} orders</span>
          <div className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`} />
            <span className="text-xs text-gray-500">{connected ? 'Live' : 'Reconnecting...'}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-lg font-mono text-white">
            {currentTime.toLocaleTimeString()}
          </span>
          <button
            onClick={loadOrders}
            className="px-4 py-2 bg-orange-500 rounded hover:bg-orange-600 text-sm text-white"
          >
            Refresh
          </button>
        </div>
      </header>

      {/* Orders Grid */}
      <div className="flex-1 overflow-auto p-4">
        {orders.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="text-6xl mb-4">👨‍🍳</div>
            <div className="text-xl">No pending orders</div>
            <div className="text-sm mt-2">New orders will appear here automatically</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {orders.map(order => (
              <div
                key={order.order_id}
                className={`bg-gray-800 rounded-lg border-l-4 ${priorityColors[order.items[0]?.priority || 'normal']} shadow-lg`}
              >
                {/* Order Header */}
                <div className="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-orange-400">
                      #{order.order_number}
                    </span>
                    <span className="text-lg" title={order.order_type}>
                      {orderTypeIcons[order.order_type] || '🍽️'}
                    </span>
                    {order.table_id && (
                      <span className="text-sm bg-gray-700 px-2 py-0.5 rounded text-gray-300">
                        T{order.table_id}
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">
                      {getTimeSince(order.created_at)}
                    </div>
                  </div>
                </div>

                {/* Items */}
                <div className="px-4 py-2 space-y-2">
                  {order.items.map(item => {
                    const timer = getPrepTimer(item)
                    const overdue = isOverdue(item)
                    return (
                      <div
                        key={item.id}
                        className={`flex items-center justify-between py-2 px-3 rounded transition-colors ${
                          item.prep_status === 'ready' ? 'bg-green-900/30' :
                          overdue ? 'bg-red-900/30 animate-pulse' :
                          item.prep_status === 'preparing' ? 'bg-blue-900/20' : ''
                        }`}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-lg text-white">{item.quantity}x</span>
                            <span className={`${
                              item.prep_status === 'ready' ? 'line-through text-gray-500' : 'text-white'
                            }`}>
                              {item.item_name}
                            </span>
                          </div>
                          {item.cooking_instructions && (
                            <p className="text-sm text-yellow-400 mt-1">
                              📝 {item.cooking_instructions}
                            </p>
                          )}
                          {timer && (
                            <span className={`text-xs font-mono ${overdue ? 'text-red-400 font-bold' : 'text-blue-400'}`}>
                              ⏱ {timer}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1 ml-2">
                          {item.prep_status === 'pending' && (
                            <button
                              onClick={() => updateItemStatus(item.id, 'preparing')}
                              className="px-4 py-2 bg-blue-500 rounded text-sm hover:bg-blue-600 text-white font-medium min-w-[70px]"
                            >
                              Start
                            </button>
                          )}
                          {item.prep_status === 'preparing' && (
                            <button
                              onClick={() => updateItemStatus(item.id, 'ready')}
                              className="px-4 py-2 bg-green-500 rounded text-sm hover:bg-green-600 text-white font-medium min-w-[70px]"
                            >
                              Ready
                            </button>
                          )}
                          {item.prep_status === 'ready' && (
                            <span className="px-4 py-2 text-green-400 text-sm font-medium">✓ Done</span>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <footer className="bg-gray-800 px-6 py-2 flex justify-between items-center border-t border-gray-700 text-sm">
        <div className="flex gap-6 text-gray-400">
          <span>Pending: <span className="text-yellow-400 font-bold">{orders.reduce((s, o) => s + o.items.filter(i => i.prep_status === 'pending').length, 0)}</span></span>
          <span>Preparing: <span className="text-blue-400 font-bold">{orders.reduce((s, o) => s + o.items.filter(i => i.prep_status === 'preparing').length, 0)}</span></span>
          <span>Ready: <span className="text-green-400 font-bold">{orders.reduce((s, o) => s + o.items.filter(i => i.prep_status === 'ready').length, 0)}</span></span>
        </div>
        <div className="text-gray-500">
          {connected ? '🟢 Connected' : '🔴 Disconnected - using polling'}
        </div>
      </footer>
    </div>
  )
}
