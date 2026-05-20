import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface InventoryItem {
  id: string
  name: string
  item_code: string | null
  unit: string
  current_stock: number
  minimum_stock: number
  reorder_level: number | null
  cost_price: number
  selling_price: number | null
  category_id: string | null
  supplier_id: string | null
  is_trackable: boolean
  expires_on: string | null
  is_active: boolean
}

interface StockMovement {
  id: string
  inventory_item_id: string
  movement_type: string
  quantity: number
  batch_number: string | null
  notes: string | null
  created_at: string
}

interface Vendor {
  id: string
  name: string
}

interface PurchaseOrder {
  id: string
  order_number: string
  vendor_id: string
  status: string
  subtotal: number
  tax_amount: number
  total: number
  expected_delivery: string | null
  notes: string | null
  created_at: string
}

interface ItemForm {
  name: string
  item_code: string
  unit: string
  current_stock: string
  minimum_stock: string
  cost_price: string
  selling_price: string
  category_id: string
}

interface AdjustmentForm {
  inventory_item_id: string
  quantity: string
  movement_type: string
  notes: string
  batch_number: string
}

const emptyItemForm: ItemForm = { name: '', item_code: '', unit: 'kg', current_stock: '0', minimum_stock: '0', cost_price: '', selling_price: '', category_id: '' }
const emptyAdjustment: AdjustmentForm = { inventory_item_id: '', quantity: '', movement_type: 'adjustment_in', notes: '', batch_number: '' }

export default function Inventory() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [lowStock, setLowStock] = useState<InventoryItem[]>([])
  const [movements, setMovements] = useState<StockMovement[]>([])
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [purchaseOrders, setPurchaseOrders] = useState<PurchaseOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'items' | 'movements' | 'orders'>('items')
  const [showItemForm, setShowItemForm] = useState(false)
  const [showAdjustment, setShowAdjustment] = useState(false)
  const [showPOForm, setShowPOForm] = useState(false)
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null)
  const [itemForm, setItemForm] = useState<ItemForm>(emptyItemForm)
  const [adjForm, setAdjForm] = useState<AdjustmentForm>(emptyAdjustment)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // PO form state
  const [poForm, setPoForm] = useState({ vendor_id: '', expected_delivery: '', notes: '', items: [{ inventory_item_id: '', quantity: '', unit_price: '' }] })

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [itemsRes, lowRes, vendorsRes, poRes] = await Promise.all([
        apiClient.get('/inventory/items'),
        apiClient.get('/inventory/low-stock').catch(() => ({ data: [] })),
        apiClient.get('/vendors/').catch(() => ({ data: [] })),
        apiClient.get('/purchase-orders/').catch(() => ({ data: [] })),
      ])
      setItems(itemsRes.data)
      setLowStock(lowRes.data)
      setVendors(vendorsRes.data)
      setPurchaseOrders(poRes.data)
    } catch (err) {
      console.error('Failed to load inventory', err)
    } finally {
      setLoading(false)
    }
  }

  // Item CRUD
  const openCreateItem = () => { setItemForm(emptyItemForm); setEditingItem(null); setShowItemForm(true); setError(null) }
  const openEditItem = (item: InventoryItem) => {
    setItemForm({ name: item.name, item_code: item.item_code || '', unit: item.unit, current_stock: String(item.current_stock), minimum_stock: String(item.minimum_stock), cost_price: String(item.cost_price), selling_price: item.selling_price ? String(item.selling_price) : '', category_id: item.category_id || '' })
    setEditingItem(item); setShowItemForm(true); setError(null)
  }

  const saveItem = async () => {
    if (!itemForm.name) { setError('Name required'); return }
    setSaving(true); setError(null)
    try {
      const payload = { ...itemForm, current_stock: parseFloat(itemForm.current_stock) || 0, minimum_stock: parseFloat(itemForm.minimum_stock) || 0, cost_price: parseFloat(itemForm.cost_price) || 0, selling_price: itemForm.selling_price ? parseFloat(itemForm.selling_price) : null, category_id: itemForm.category_id || null }
      if (editingItem) { await apiClient.put(`/inventory/items/${editingItem.id}`, payload) }
      else { await apiClient.post('/inventory/items', payload) }
      setShowItemForm(false); loadData()
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to save') } finally { setSaving(false) }
  }

  const deleteItem = async (id: string) => {
    if (!confirm('Delete this inventory item?')) return
    try { await apiClient.delete(`/inventory/items/${id}`); setItems(items.filter(i => i.id !== id)) } catch { /* silent */ }
  }

  // Stock Adjustment
  const openAdjustment = (itemId?: string) => {
    setAdjForm({ ...emptyAdjustment, inventory_item_id: itemId || '' }); setShowAdjustment(true); setError(null)
  }

  const saveAdjustment = async () => {
    if (!adjForm.inventory_item_id || !adjForm.quantity) { setError('Item and quantity required'); return }
    setSaving(true); setError(null)
    try {
      await apiClient.post('/inventory/stock-movements', {
        inventory_item_id: adjForm.inventory_item_id,
        movement_type: adjForm.movement_type,
        quantity: parseFloat(adjForm.quantity),
        notes: adjForm.notes || null,
        batch_number: adjForm.batch_number || null,
      })
      setShowAdjustment(false); loadData()
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to save') } finally { setSaving(false) }
  }

  // Purchase Orders
  const addPOItem = () => { setPoForm({ ...poForm, items: [...poForm.items, { inventory_item_id: '', quantity: '', unit_price: '' }] }) }
  const removePOItem = (idx: number) => { setPoForm({ ...poForm, items: poForm.items.filter((_, i) => i !== idx) }) }

  const savePO = async () => {
    if (!poForm.vendor_id || poForm.items.length === 0) { setError('Vendor and items required'); return }
    setSaving(true); setError(null)
    try {
      await apiClient.post('/purchase-orders/', {
        vendor_id: poForm.vendor_id,
        branch_id: '', // Will use user's branch
        expected_delivery: poForm.expected_delivery || null,
        notes: poForm.notes || null,
        items: poForm.items.map(i => ({ inventory_item_id: i.inventory_item_id, quantity: parseFloat(i.quantity), unit_price: parseFloat(i.unit_price) })),
      })
      setShowPOForm(false); loadData()
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to create PO') } finally { setSaving(false) }
  }

  const approvePO = async (id: string) => {
    try { await apiClient.post(`/purchase-orders/${id}/approve`); loadData() } catch { /* silent */ }
  }

  const receivePO = async (id: string) => {
    try { await apiClient.post(`/purchase-orders/${id}/receive`); loadData() } catch { /* silent */ }
  }

  const statusColors: Record<string, string> = { draft: 'bg-gray-100 text-gray-700', approved: 'bg-blue-100 text-blue-700', received: 'bg-green-100 text-green-700' }

  if (loading) return <div className="p-6 text-gray-500">Loading inventory...</div>

  return (
    <div>
      {/* Tabs */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          {(['items', 'movements', 'orders'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`pb-2 font-medium capitalize ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>
              {t === 'orders' ? 'Purchase Orders' : t === 'movements' ? 'Stock Movements' : `Items (${items.length})`}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {tab === 'items' && <button onClick={openCreateItem} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">+ Add Item</button>}
          {tab === 'items' && <button onClick={() => openAdjustment()} className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 text-sm">Stock Adjustment</button>}
          {tab === 'orders' && <button onClick={() => setShowPOForm(true)} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">+ New PO</button>}
        </div>
      </div>

      {/* Low Stock Alert */}
      {lowStock.length > 0 && tab === 'items' && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h4 className="text-red-700 font-semibold mb-2">Low Stock Alert ({lowStock.length} items)</h4>
          <div className="flex flex-wrap gap-2">
            {lowStock.map(item => (
              <span key={item.id} className="bg-red-100 text-red-700 px-2 py-1 rounded text-sm">{item.name} ({item.current_stock} {item.unit})</span>
            ))}
          </div>
        </div>
      )}

      {/* Items Table */}
      {tab === 'items' && (
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
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.length === 0 ? (
                <tr><td colSpan={7} className="px-6 py-4 text-center text-gray-500">No inventory items. Add your first item.</td></tr>
              ) : items.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{item.name}</td>
                  <td className="px-6 py-4 text-gray-500">{item.item_code || '-'}</td>
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
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => openAdjustment(item.id)} className="text-orange-500 hover:text-orange-700 text-sm mr-3">Adjust</button>
                    <button onClick={() => openEditItem(item)} className="text-blue-500 hover:text-blue-700 text-sm mr-3">Edit</button>
                    <button onClick={() => deleteItem(item.id)} className="text-red-500 hover:text-red-700 text-sm">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stock Movements */}
      {tab === 'movements' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {movements.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No stock movements yet</td></tr>
              ) : movements.map(m => (
                <tr key={m.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">{items.find(i => i.id === m.inventory_item_id)?.name || m.inventory_item_id}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${m.movement_type.includes('in') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{m.movement_type}</span></td>
                  <td className="px-6 py-4">{m.quantity}</td>
                  <td className="px-6 py-4 text-gray-500">{m.batch_number || '-'}</td>
                  <td className="px-6 py-4 text-gray-500">{m.notes || '-'}</td>
                  <td className="px-6 py-4 text-gray-500">{new Date(m.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Purchase Orders */}
      {tab === 'orders' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">PO Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delivery</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {purchaseOrders.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No purchase orders</td></tr>
              ) : purchaseOrders.map(po => (
                <tr key={po.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{po.order_number}</td>
                  <td className="px-6 py-4">{vendors.find(v => v.id === po.vendor_id)?.name || po.vendor_id}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[po.status] || ''}`}>{po.status}</span></td>
                  <td className="px-6 py-4 text-right">₹{Number(po.total).toFixed(2)}</td>
                  <td className="px-6 py-4 text-gray-500">{po.expected_delivery || '-'}</td>
                  <td className="px-6 py-4 text-right">
                    {po.status === 'draft' && <button onClick={() => approvePO(po.id)} className="text-blue-500 hover:text-blue-700 text-sm mr-3">Approve</button>}
                    {po.status === 'approved' && <button onClick={() => receivePO(po.id)} className="text-green-500 hover:text-green-700 text-sm">Receive</button>}
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
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">{editingItem ? 'Edit Item' : 'Add Inventory Item'}</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Name *</label><input value={itemForm.name} onChange={e => setItemForm({...itemForm, name: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Code</label><input value={itemForm.item_code} onChange={e => setItemForm({...itemForm, item_code: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Unit</label><select value={itemForm.unit} onChange={e => setItemForm({...itemForm, unit: e.target.value})} className="w-full px-3 py-2 border rounded"><option>kg</option><option>g</option><option>l</option><option>ml</option><option>pcs</option><option>box</option></select></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Current Stock</label><input type="number" value={itemForm.current_stock} onChange={e => setItemForm({...itemForm, current_stock: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Minimum Stock</label><input type="number" value={itemForm.minimum_stock} onChange={e => setItemForm({...itemForm, minimum_stock: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Cost Price</label><input type="number" value={itemForm.cost_price} onChange={e => setItemForm({...itemForm, cost_price: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Selling Price</label><input type="number" value={itemForm.selling_price} onChange={e => setItemForm({...itemForm, selling_price: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveItem} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">{saving ? 'Saving...' : 'Save'}</button>
              <button onClick={() => setShowItemForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Adjustment Modal */}
      {showAdjustment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Stock Adjustment</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Item *</label>
                <select value={adjForm.inventory_item_id} onChange={e => setAdjForm({...adjForm, inventory_item_id: e.target.value})} className="w-full px-3 py-2 border rounded">
                  <option value="">Select item...</option>
                  {items.map(i => <option key={i.id} value={i.id}>{i.name} ({i.current_stock} {i.unit})</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select value={adjForm.movement_type} onChange={e => setAdjForm({...adjForm, movement_type: e.target.value})} className="w-full px-3 py-2 border rounded">
                  <option value="adjustment_in">Stock In (+)</option>
                  <option value="adjustment_out">Stock Out (-)</option>
                  <option value="waste">Waste</option>
                  <option value="return">Return</option>
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label><input type="number" value={adjForm.quantity} onChange={e => setAdjForm({...adjForm, quantity: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Batch Number</label><input value={adjForm.batch_number} onChange={e => setAdjForm({...adjForm, batch_number: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={adjForm.notes} onChange={e => setAdjForm({...adjForm, notes: e.target.value})} className="w-full px-3 py-2 border rounded" placeholder="Reason for adjustment" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveAdjustment} disabled={saving} className="flex-1 bg-orange-500 text-white py-2 rounded hover:bg-orange-600 disabled:opacity-50">{saving ? 'Saving...' : 'Adjust Stock'}</button>
              <button onClick={() => setShowAdjustment(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Purchase Order Form Modal */}
      {showPOForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-auto">
            <h3 className="text-lg font-bold mb-4">Create Purchase Order</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Vendor *</label>
                <select value={poForm.vendor_id} onChange={e => setPoForm({...poForm, vendor_id: e.target.value})} className="w-full px-3 py-2 border rounded">
                  <option value="">Select vendor...</option>
                  {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Expected Delivery</label><input type="date" value={poForm.expected_delivery} onChange={e => setPoForm({...poForm, expected_delivery: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={poForm.notes} onChange={e => setPoForm({...poForm, notes: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Items *</label>
                {poForm.items.map((item, idx) => (
                  <div key={idx} className="flex gap-2 mb-2">
                    <select value={item.inventory_item_id} onChange={e => { const newItems = [...poForm.items]; newItems[idx].inventory_item_id = e.target.value; setPoForm({...poForm, items: newItems}) }} className="flex-1 px-3 py-2 border rounded text-sm">
                      <option value="">Item...</option>
                      {items.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
                    </select>
                    <input type="number" placeholder="Qty" value={item.quantity} onChange={e => { const newItems = [...poForm.items]; newItems[idx].quantity = e.target.value; setPoForm({...poForm, items: newItems}) }} className="w-20 px-3 py-2 border rounded text-sm" />
                    <input type="number" placeholder="Price" value={item.unit_price} onChange={e => { const newItems = [...poForm.items]; newItems[idx].unit_price = e.target.value; setPoForm({...poForm, items: newItems}) }} className="w-24 px-3 py-2 border rounded text-sm" />
                    {poForm.items.length > 1 && <button onClick={() => removePOItem(idx)} className="text-red-500 px-2">✕</button>}
                  </div>
                ))}
                <button onClick={addPOItem} className="text-blue-500 text-sm hover:text-blue-700">+ Add item</button>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={savePO} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">{saving ? 'Creating...' : 'Create PO'}</button>
              <button onClick={() => setShowPOForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
