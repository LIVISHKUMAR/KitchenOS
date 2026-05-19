import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCartStore } from '../stores/cartStore'

export default function Cart() {
  const { items, removeItem, updateQuantity, getTotal, clearCart } = useCartStore()
  const navigate = useNavigate()

  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0)
  const tax = subtotal * 0.18
  const total = subtotal + tax

  if (items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-xl text-gray-500 mb-4">Your cart is empty</p>
        <Link to="/" className="text-orange-500 hover:underline">
          Browse Menu
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Your Cart</h1>

      <div className="space-y-4 mb-6">
        {items.map(item => (
          <div key={item.id} className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-lg">{item.is_veg ? '🟢' : '🔴'}</span>
              <div>
                <h3 className="font-semibold">{item.name}</h3>
                <p className="text-sm text-gray-500">₹{item.price.toFixed(2)} each</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateQuantity(item.id, item.quantity - 1)}
                  className="w-8 h-8 bg-gray-100 rounded-full hover:bg-gray-200"
                >
                  -
                </button>
                <span className="w-8 text-center font-semibold">{item.quantity}</span>
                <button
                  onClick={() => updateQuantity(item.id, item.quantity + 1)}
                  className="w-8 h-8 bg-gray-100 rounded-full hover:bg-gray-200"
                >
                  +
                </button>
              </div>
              <span className="font-bold w-20 text-right">₹{(item.price * item.quantity).toFixed(2)}</span>
              <button
                onClick={() => removeItem(item.id)}
                className="text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Subtotal</span>
            <span>₹{subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">GST (18%)</span>
            <span>₹{tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between pt-2 border-t font-bold text-lg">
            <span>Total</span>
            <span>₹{total.toFixed(2)}</span>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => clearCart()}
          className="flex-1 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Clear Cart
        </button>
        <button
          onClick={() => navigate('/checkout')}
          className="flex-1 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 font-semibold"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  )
}
