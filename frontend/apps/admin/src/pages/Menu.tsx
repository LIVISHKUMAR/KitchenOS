import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { TableRowSkeleton } from '../components/Skeleton'

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
  const queryClient = useQueryClient();
  const [showItemForm, setShowItemForm] = useState(false)
  const [showCatForm, setShowCatForm] = useState(false)
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null)
  const [editingCat, setEditingCat] = useState<Category | null>(null)
  const [form, setForm] = useState<MenuItemForm>(emptyForm)
  const [catForm, setCatForm] = useState({ name: '', description: '' })
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<'items' | 'categories'>('items')
  const [search, setSearch] = useState('')

  // React Query hooks
  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: queryKeys.menu.items(),
    queryFn: () => apiClient.get('/menu/items').then(res => res.data),
  });

  const { data: categories = [] } = useQuery({
    queryKey: queryKeys.menu.categories(),
    queryFn: () => apiClient.get('/menu/categories').then(res => res.data),
  });

  // Mutations
  const toggleAvailabilityMutation = useMutation({
    mutationFn: ({ id, is_available }: { id: string; is_available: boolean }) =>
      apiClient.put(`/menu/items/${id}`, { is_available }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.menu.items() }),
  });

  const saveItemMutation = useMutation({
    mutationFn: (data: { id?: string; payload: Record<string, unknown> }) =>
      data.id ? apiClient.put(`/menu/items/${data.id}`, data.payload) : apiClient.post('/menu/items', data.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.menu.items() });
      setShowItemForm(false);
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to save'),
  });

  const deleteItemMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/menu/items/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.menu.items() }),
  });

  const saveCategoryMutation = useMutation({
    mutationFn: (data: { id?: string; payload: Record<string, string> }) =>
      data.id ? apiClient.put(`/menu/categories/${data.id}`, data.payload) : apiClient.post('/menu/categories', data.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.menu.categories() });
      setShowCatForm(false);
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to save'),
  });

  const deleteCategoryMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/menu/categories/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.menu.categories() }),
  });

  // Filter items
  const filteredItems = items.filter((item: MenuItem) =>
    !search || item.name.toLowerCase().includes(search.toLowerCase()) ||
    (item.item_code && item.item_code.toLowerCase().includes(search.toLowerCase()))
  );

  const openCreateItem = () => {
    setForm(emptyForm); setEditingItem(null); setShowItemForm(true); setError(null)
  }

  const openEditItem = (item: MenuItem) => {
    setForm({
      name: item.name, description: item.description || '', item_code: item.item_code || '',
      base_price: String(item.base_price), cost_price: item.cost_price ? String(item.cost_price) : '',
      tax_rate: item.tax_rate ? String(item.tax_rate) : '18', is_veg: item.is_veg,
      is_available: item.is_available, category_id: item.category_id,
      preparation_time_minutes: item.preparation_time_minutes ? String(item.preparation_time_minutes) : '',
      image_url: item.image_url || '',
    })
    setEditingItem(item); setShowItemForm(true); setError(null)
  }

  const saveItem = () => {
    if (!form.name || !form.base_price || !form.category_id) {
      setError('Name, price, and category are required'); return
    }
    const payload = {
      name: form.name, description: form.description || null, item_code: form.item_code || null,
      base_price: parseFloat(form.base_price), cost_price: form.cost_price ? parseFloat(form.cost_price) : null,
      tax_rate: form.tax_rate ? parseFloat(form.tax_rate) : 18, is_veg: form.is_veg,
      is_available: form.is_available, category_id: form.category_id,
      preparation_time_minutes: form.preparation_time_minutes ? parseInt(form.preparation_time_minutes) : null,
      image_url: form.image_url || null,
    }
    saveItemMutation.mutate({ id: editingItem?.id, payload })
  }

  const saveCategory = () => {
    if (!catForm.name) return
    saveCategoryMutation.mutate({ id: editingCat?.id, payload: catForm })
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Menu Management</h2>
          <p className="text-sm text-gray-500 mt-1">{items.length} items in {categories.length} categories</p>
        </div>
        <button onClick={tab === 'items' ? openCreateItem : openCreateCat} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">
          + Add {tab === 'items' ? 'Item' : 'Category'}
        </button>
      </div>

      {/* Tabs + Search */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-4">
          <button onClick={() => setTab('items')} className={`pb-2 font-medium transition-colors ${tab === 'items' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            Items ({items.length})
          </button>
          <button onClick={() => setTab('categories')} className={`pb-2 font-medium transition-colors ${tab === 'categories' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            Categories ({categories.length})
          </button>
        </div>
        {tab === 'items' && (
          <input
            type="text"
            placeholder="Search items..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64"
          />
        )}
      </div>

      {/* Items Table */}
      {tab === 'items' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {itemsLoading ? (
                <>
                  <TableRowSkeleton columns={6} />
                  <TableRowSkeleton columns={6} />
                  <TableRowSkeleton columns={6} />
                </>
              ) : filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                    <div className="text-4xl mb-2">🍽️</div>
                    <p className="text-lg font-medium">No menu items</p>
                    <p className="text-sm mt-1">{search ? 'No items match your search' : 'Add your first item to get started'}</p>
                  </td>
                </tr>
              ) : (
                filteredItems.map((item: MenuItem) => (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {item.image_url ? (
                          <img src={item.image_url} alt={item.name} className="w-10 h-10 rounded-lg object-cover" />
                        ) : (
                          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-lg">
                            {item.is_veg ? '🟢' : '🔴'}
                          </div>
                        )}
                        <div>
                          <div className="font-medium text-gray-900">{item.name}</div>
                          {item.item_code && <div className="text-xs text-gray-400">{item.item_code}</div>}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {categories.find((c: Category) => c.id === item.category_id)?.name || '-'}
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">₹{Number(item.base_price).toFixed(2)}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${item.is_veg ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {item.is_veg ? 'Veg' : 'Non-veg'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => toggleAvailabilityMutation.mutate({ id: item.id, is_available: !item.is_available })}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${item.is_available ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-red-100 text-red-700 hover:bg-red-200'}`}
                      >
                        {item.is_available ? 'Available' : 'Unavailable'}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => openEditItem(item)} className="text-blue-500 hover:text-blue-700 text-sm font-medium mr-3">Edit</button>
                      <button onClick={() => { if (confirm('Delete this item?')) deleteItemMutation.mutate(item.id) }} className="text-red-500 hover:text-red-700 text-sm font-medium">Delete</button>
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
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Items</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {categories.map((cat: Category) => (
                <tr key={cat.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900">{cat.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{cat.description || '-'}</td>
                  <td className="px-6 py-4 text-right text-sm">{items.filter((i: MenuItem) => i.category_id === cat.id).length}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => { setCatForm({ name: cat.name, description: cat.description || '' }); setEditingCat(cat); setShowCatForm(true) }} className="text-blue-500 hover:text-blue-700 text-sm font-medium mr-3">Edit</button>
                    <button onClick={() => { if (confirm('Delete this category?')) deleteCategoryMutation.mutate(cat.id) }} className="text-red-500 hover:text-red-700 text-sm font-medium">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Item Form Modal */}
      {showItemForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-auto shadow-2xl">
            <h3 className="text-lg font-bold mb-4">{editingItem ? 'Edit Menu Item' : 'Add Menu Item'}</h3>
            {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Item Code</label>
                  <input value={form.item_code} onChange={e => setForm({...form, item_code: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="For barcode scanning" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                  <select value={form.category_id} onChange={e => setForm({...form, category_id: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                    <option value="">Select...</option>
                    {categories.map((c: Category) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Price (₹) *</label>
                  <input type="number" value={form.base_price} onChange={e => setForm({...form, base_price: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cost (₹)</label>
                  <input type="number" value={form.cost_price} onChange={e => setForm({...form, cost_price: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tax %</label>
                  <input type="number" value={form.tax_rate} onChange={e => setForm({...form, tax_rate: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Prep Time (min)</label>
                  <input type="number" value={form.preparation_time_minutes} onChange={e => setForm({...form, preparation_time_minutes: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
                  <input value={form.image_url} onChange={e => setForm({...form, image_url: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="https://..." />
                </div>
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.is_veg} onChange={e => setForm({...form, is_veg: e.target.checked})} className="rounded" />
                  <span className="text-sm">Vegetarian</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.is_available} onChange={e => setForm({...form, is_available: e.target.checked})} className="rounded" />
                  <span className="text-sm">Available</span>
                </label>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveItem} disabled={saveItemMutation.isPending} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
                {saveItemMutation.isPending ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setShowItemForm(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg hover:bg-gray-200 font-medium">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Category Form Modal */}
      {showCatForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            <h3 className="text-lg font-bold mb-4">{editingCat ? 'Edit Category' : 'Add Category'}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input value={catForm.name} onChange={e => setCatForm({...catForm, name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={catForm.description} onChange={e => setCatForm({...catForm, description: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" rows={2} />
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveCategory} disabled={saveCategoryMutation.isPending} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">
                {saveCategoryMutation.isPending ? 'Saving...' : 'Save'}
              </button>
              <button onClick={() => setShowCatForm(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg hover:bg-gray-200 font-medium">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
