import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import apiClient from '../api/client'

interface Order {
  id: string
  order_number: string
  status: string
  total: number
  items: Array<{
    item_name: string
    quantity: number
    prep_status: string
  }>
  created_at: string
}

export default function OrderTracking() {
  const { orderId } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadOrder()
    const interval = setInterval(loadOrder, 10000) // Poll every 10s
    return () => clearInterval(interval)
  }, [orderId])

  const loadOrder = async () => {
    try {
      const res = await apiClient.get(`/orders/${orderId}`)
      setOrder(res.data)
    } catch (err) {
      console.error('Failed to load order', err)
    } finally {
      setLoading(false)
    }
  }

  const statusSteps = ['pending', 'confirmed', 'preparing', 'ready', 'completed']

  if (loading) return <div className="text-center py-12">Loading...</div>
  if (!order) return <div className="text-center py-12">Order not found</div>

  const currentIndex = statusSteps.indexOf(order.status)

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2">Order #{order.order_number}</h1>
        <p className="text-gray-500">
          {new Date(order.created_at).toLocaleString()}
        </p>
      </div>

      {/* Status Progress */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex justify-between mb-4">
          {statusSteps.map((step, i) => (
            <div
              key={step}
              className={`flex flex-col items-center ${
                i <= currentIndex ? 'text-orange-500' : 'text-gray-300'
              }`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
                i <= currentIndex ? 'bg-orange-500 text-white' : 'bg-gray-200'
              }`}>
                {i < currentIndex ? '✓' : i + 1}
              </div>
              <span className="text-xs capitalize">{step}</span>
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-orange-500 h-2 rounded-full transition-all"
            style={{ width: `${(currentIndex / (statusSteps.length - 1)) * 100}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6 text-center">
        {order.status === 'pending' && <p className="text-lg">Your order has been received!</p>}
        {order.status === 'confirmed' && <p className="text-lg">Your order is confirmed!</p>}
        {order.status === 'preparing' && <p className="text-lg text-orange-500">Your food is being prepared...</p>}
        {order.status === 'ready' && <p className="text-lg text-green-500">Your order is ready!</p>}
        {order.status === 'completed' && <p className="text-lg text-green-600">Order completed. Enjoy your meal!</p>}
      </div>

      {/* Items */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <h2 className="font-semibold mb-3">Items</h2>
        <div className="space-y-2">
          {order.items.map((item, i) => (
            <div key={i} className="flex justify-between">
              <span>{item.item_name} x{item.quantity}</span>
              <span className={`text-sm ${
                item.prep_status === 'ready' ? 'text-green-500' : 'text-gray-500'
              }`}>
                {item.prep_status}
              </span>
            </div>
          ))}
        </div>
        <div className="border-t mt-4 pt-4 font-bold flex justify-between">
          <span>Total</span>
          <span>₹{Number(order.total).toFixed(2)}</span>
        </div>
      </div>

      <div className="text-center">
        <Link to="/" className="text-orange-500 hover:underline">
          Order More
        </Link>
      </div>
    </div>
  )
}
