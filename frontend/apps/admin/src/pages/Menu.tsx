import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface MenuItem {
  id: string
  name: string
  description: string | null
  item_code: string | null
  base_price: number
  cost_price: number | null
  tax_rate: number | null
  is_veg: boolean
  is_available: boolean
  is_combo: boolean
  category_id: string
  preparation_time_minutes: number | null
  image_url: string | null
}

interface Category {
  id: string
  name: string
  description: string | null
  display_order: number
  is_active: boolean
}

interface MenuItemForm {
  name: string
  description: string
  item_code: string
  base_price: string
  cost_price: string
  tax_rate: string
  is_veg: boolean
  is_available: boolean
  category_id: string
  preparation_time_minutes: string
  image_url: string
}

const emptyForm: MenuItemForm = {
  name: '', description: '', item_code: '', base_price: '', cost_price: '',
  tax_rate: '18', is_veg: true, is_available: true, category_id: '',
  preparation_time_minutes: '', image_url: '',
}

export default function Menu() {
  const [items, setItems] = useState<MenuItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [showItemForm, setShowItemForm] = useState(false)
  const [showCatForm, setShowCatForm] = useState(false)
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null)
  const [editingCat, setEditingCat] = useState<Category | null>(null)
  const [form, setForm] = useState<MenuItemForm>(emptyForm)
  const [catForm, setCatForm] = useState({ name: '', description: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'items' | 'categories'>('items')

  useEffect(() => { loadData() }, [])

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

  const openCreateItem = () => {
    setForm(emptyForm)
    setEditingItem(null)
    setShowItemForm(true)
    setError(null)
  }

  const openEditItem = (item: MenuItem) => {
    setForm({
      name: item.name,
      description: item.description || '',
      item_code: item.item_code || '',
      base_price: String(item.base_price),
      cost_price: item.cost_price ? String(item.cost_price) : '',
      tax_rate: item.tax_rate ? String(item.tax_rate) : '18',
      is_veg: item.is_veg,
      is_available: item.is_available,
      category_id: item.category_id,
      preparation_time_minutes: item.preparation_time_minutes ? String(item.preparation_time_minutes) : '',
      image_url: item.image_url || '',
    })
    setEditingItem(item)
    setShowItemForm(true)
    setError(null)
  }

  const saveItem = async () => {
    if (!form.name || !form.base_price || !form.category_id) {
      setError('Name, price, and category are required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        item_code: form.item_code || null,
        base_price: parseFloat(form.base_price),
        cost_price: form.cost_price ? parseFloat(form.cost_price) : null,
        tax_rate: form.tax_rate ? parseFloat(form.tax_rate) : 18,
        is_veg: form.is_veg,
        is_available: form.is_available,
        category_id: form.category_id,
        preparation_time_minutes: form.preparation_time_minutes ? parseInt(form.preparation_time_minutes) : null,
        image_url: form.image_url || null,
      }
      if (editingItem) {
        await apiClient.put(`/menu/items/${editingItem.id}`, payload)
      } else {
        await apiClient.post('/menu/items', payload)
      }
      setShowItemForm(false)
      loadData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const deleteItem = async (id: string) => {
    if (!confirm('Delete this menu item?')) return
    try {
      await apiClient.delete(`/menu/items/${id}`)
      setItems(items.filter(i => i.id !== id))
    } catch (err) {
      console.error('Failed to delete', err)
    }
  }

  const openCreateCat = () => {
    setCatForm({ name: '', description: '' })
    setEditingCat(null)
    setShowCatForm(true)
  }

  const openEditCat = (cat: Category) => {
    setCatForm({ name: cat.name, description: cat.description || '' })
    setEditingCat(cat)
    setShowCatForm(true)
  }

  const saveCategory = async () => {
    if (!catForm.name) return
    setSaving(true)
    try {
      if (editingCat) {
        await apiClient.put(`/menu/categories/${editingCat.id}`, catForm)
      } else {
        await apiClient.post('/menu/categories', catForm)
      }
      setShowCatForm(false)
      loadData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const deleteCategory = async (id: string) => {
    if (!confirm('Delete this category? Items in it will be unassigned.')) return
    try {
      await apiClient.delete(`/menu/categories/${id}`)
      setCategories(categories.filter(c => c.id !== id))
    } catch (err) {
      console.error('Failed to delete', err)
    }
  }

  return (
    <div>
      {/* Tabs */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          <button
            onClick={() => setTab('items')}
            className={`pb-2 font-medium ${tab === 'items' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
          >
            Menu Items ({items.length})
          </button>
          <button
            onClick={() => setTab('categories')}
            className={`pb-2 font-medium ${tab === 'categories' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}
          >
            Categories ({categories.length})
          </button>
        </div>
        <button
          onClick={tab === 'items' ? openCreateItem : openCreateCat}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm"
        >
          + Add {tab === 'items' ? 'Item' : 'Category'}
        </button>
      </div>

      {/* Items Table */}
      {tab === 'items' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Available</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center">Loading...</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No menu items. Add your first item.</td></tr>
              ) : (
                items.map(item => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-medium">{item.name}</div>
                      {item.item_code && <div className="text-xs text-gray-400">{item.item_code}</div>}
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {categories.find(c => c.id === item.category_id)?.name || '-'}
                    </td>
                    <td className="px-6 py-4">₹{Number(item.base_price).toFixed(2)}</td>
                    <td className="px-6 py-4">{item.is_veg ? '🟢 Veg' : '🔴 Non-veg'}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleAvailability(item.id, item.is_available)}
                        className={`px-3 py-1 rounded-full text-xs ${item.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                      >
                        {item.is_available ? 'Available' : 'Unavailable'}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => openEditItem(item)} className="text-blue-500 hover:text-blue-700 text-sm mr-3">Edit</button>
                      <button onClick={() => deleteItem(item.id)} className="text-red-500 hover:text-red-700 text-sm">Delete</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Categories Table */}
      {tab === 'categories' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {categories.map(cat => (
                <tr key={cat.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{cat.name}</td>
                  <td className="px-6 py-4 text-gray-500">{cat.description || '-'}</td>
                  <td className="px-6 py-4">{items.filter(i => i.category_id === cat.id).length}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => openEditCat(cat)} className="text-blue-500 hover:text-blue-700 text-sm mr-3">Edit</button>
                    <button onClick={() => deleteCategory(cat.id)} className="text-red-500 hover:text-red-700 text-sm">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Item Form Modal */}
      {showItemForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-auto">
            <h3 className="text-lg font-bold mb-4">{editingItem ? 'Edit Menu Item' : 'Add Menu Item'}</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full px-3 py-2 border rounded" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full px-3 py-2 border rounded" rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Item Code</label>
                  <input value={form.item_code} onChange={e => setForm({...form, item_code: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                  <select value={form.category_id} onChange={e => setForm({...form, category_id: e.target.value})} className="w-full px-3 py-2 border rounded">
                    <option value="">Select...</option>
                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
                  <input type="number" value={form.base_price} onChange={e => setForm({...form, base_price: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cost Price</label>
                  <input type="number" value={form.cost_price} onChange={e => setForm({...form, cost_price: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax %</label>
                  <input type="number" value={form.tax_rate} onChange={e => setForm({...form, tax_rate: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prep Time (min)</label>
                  <input type="number" value={form.preparation_time_minutes} onChange={e => setForm({...form, preparation_time_minutes: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
                  <input value={form.image_url} onChange={e => setForm({...form, image_url: e.target.value})} className="w-full px-3 py-2 border rounded" />
                </div>
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={form.is_veg} onChange={e => setForm({...form, is_veg: e.target.checked})} />
                  <span className="text-sm">Vegetarian</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={form.is_available} onChange={e => setForm({...form, is_available: e.target.checked})} />
                  <span className="text-sm">Available</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveItem} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setShowItemForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Category Form Modal */}
      {showCatForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-bold mb-4">{editingCat ? 'Edit Category' : 'Add Category'}</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input value={catForm.name} onChange={e => setCatForm({...catForm, name: e.target.value})} className="w-full px-3 py-2 border rounded" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={catForm.description} onChange={e => setCatForm({...catForm, description: e.target.value})} className="w-full px-3 py-2 border rounded" rows={2} />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveCategory} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setShowCatForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
