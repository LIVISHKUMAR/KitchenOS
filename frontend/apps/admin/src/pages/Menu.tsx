import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface MenuItem {
  id: string
  name: string
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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [itemsRes, catsRes] = await Promise.all([
        apiClient.get('/menu/items'),
        apiClient.get('/menu/categories'),
      ])
      setItems(itemsRes.data)
      setCategories(catsRes.data)
    } catch (err) {
      console.error('Failed to load menu', err)
    } finally {
      setLoading(false)
    }
  }

  const toggleAvailability = async (id: string, current: boolean) => {
    try {
      await apiClient.put(`/menu/items/${id}`, { is_available: !current })
      setItems(items.map(i => i.id === id ? { ...i, is_available: !current } : i))
    } catch (err) {
      console.error('Failed to update', err)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Menu Items ({items.length})</h3>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Available</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-4 text-center">Loading...</td></tr>
            ) : (
              items.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{item.name}</td>
                  <td className="px-6 py-4 text-gray-500">
                    {categories.find(c => c.id === item.category_id)?.name || '-'}
                  </td>
                  <td className="px-6 py-4">₹{Number(item.base_price).toFixed(2)}</td>
                  <td className="px-6 py-4">{item.is_veg ? '🟢 Veg' : '🔴 Non-veg'}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => toggleAvailability(item.id, item.is_available)}
                      className={`px-3 py-1 rounded-full text-xs ${
                        item.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {item.is_available ? 'Available' : 'Unavailable'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
