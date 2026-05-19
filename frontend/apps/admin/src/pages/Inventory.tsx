import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface InventoryItem {
  id: string
  name: string
  item_code: string
  unit: string
  current_stock: number
  minimum_stock: number
  cost_price: number
}

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [lowStock, setLowStock] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState<'all' | 'low'>('all')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [itemsRes, lowRes] = await Promise.all([
        apiClient.get('/inventory/items'),
        apiClient.get('/inventory/low-stock'),
      ])
      setItems(itemsRes.data)
      setLowStock(lowRes.data)
    } catch (err) {
      console.error('Failed to load inventory', err)
    } finally {
      setLoading(false)
    }
  }

  const displayItems = view === 'low' ? lowStock : items

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Inventory</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setView('all')}
            className={`px-4 py-2 rounded-lg text-sm ${view === 'all' ? 'bg-blue-500 text-white' : 'bg-white'}`}
          >
            All Items ({items.length})
          </button>
          <button
            onClick={() => setView('low')}
            className={`px-4 py-2 rounded-lg text-sm ${view === 'low' ? 'bg-red-500 text-white' : 'bg-white'}`}
          >
            Low Stock ({lowStock.length})
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center">Loading...</td></tr>
            ) : displayItems.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No items</td></tr>
            ) : (
              displayItems.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{item.name}</td>
                  <td className="px-6 py-4 text-gray-500">{item.item_code}</td>
                  <td className="px-6 py-4">{item.current_stock} {item.unit}</td>
                  <td className="px-6 py-4">{item.minimum_stock} {item.unit}</td>
                  <td className="px-6 py-4">₹{Number(item.cost_price).toFixed(2)}</td>
                  <td className="px-6 py-4">
                    {item.current_stock <= item.minimum_stock ? (
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">Low</span>
                    ) : (
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">OK</span>
                    )}
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
