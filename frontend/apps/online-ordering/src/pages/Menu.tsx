import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'
import { useCartStore } from '../stores/cartStore'

interface MenuItem {
  id: string
  name: string
  description: string
  base_price: number
  is_veg: boolean
  is_available: boolean
  category_id: string
}

interface Category {
  id: string
  name: string
}

export default function Menu() {
  const [items, setItems] = useState<MenuItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const addItem = useCartStore(state => state.addItem)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [itemsRes, catsRes] = await Promise.all([
        apiClient.get('/menu/items'),
        apiClient.get('/menu/categories'),
      ])
      setItems(itemsRes.data.filter((i: MenuItem) => i.is_available))
      setCategories(catsRes.data.filter((c: Category) => true))
    } catch (err) {
      console.error('Failed to load menu', err)
    } finally {
      setLoading(false)
    }
  }

  const filtered = selectedCategory
    ? items.filter(i => i.category_id === selectedCategory)
    : items

  if (loading) {
    return <div className="text-center py-12">Loading menu...</div>
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6">Our Menu</h1>

      {/* Categories */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-4 py-2 rounded-full whitespace-nowrap ${
            !selectedCategory ? 'bg-orange-500 text-white' : 'bg-white text-gray-600'
          }`}
        >
          All
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-4 py-2 rounded-full whitespace-nowrap ${
              selectedCategory === cat.id ? 'bg-orange-500 text-white' : 'bg-white text-gray-600'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map(item => (
          <div key={item.id} className="bg-white rounded-lg shadow-sm p-4 flex gap-4">
            <div className="flex-shrink-0 w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-xl">
              {item.is_veg ? '🟢' : '🔴'}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">{item.name}</h3>
              {item.description && (
                <p className="text-sm text-gray-500 mt-1 line-clamp-2">{item.description}</p>
              )}
              <div className="flex justify-between items-center mt-3">
                <span className="font-bold text-lg">₹{Number(item.base_price).toFixed(2)}</span>
                <button
                  onClick={() => addItem({
                    id: item.id,
                    name: item.name,
                    price: Number(item.base_price),
                    is_veg: item.is_veg,
                  })}
                  className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm"
                >
                  Add to Cart
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No items available in this category
        </div>
      )}
    </div>
  )
}
