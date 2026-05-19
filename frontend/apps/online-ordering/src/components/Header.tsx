import React from 'react'
import { Link } from 'react-router-dom'
import { useCartStore } from '../stores/cartStore'

export default function Header() {
  const itemCount = useCartStore(state => state.getItemCount())

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-orange-500">
          KitchenOS
        </Link>
        <Link
          to="/cart"
          className="relative px-4 py-2 bg-orange-500 text-white rounded-full hover:bg-orange-600"
        >
          Cart
          {itemCount > 0 && (
            <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
              {itemCount}
            </span>
          )}
        </Link>
      </div>
    </header>
  )
}
