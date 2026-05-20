import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { TableRowSkeleton } from '../components/Skeleton'

interface InventoryItem {
  id: string; name: string; item_code: string | null; unit: string;
  current_stock: number; minimum_stock: number; reorder_level: number | null;
  cost_price: number; selling_price: number | null; category_id: string | null;
  supplier_id: string | null; is_trackable: boolean; expires_on: string | null; is_active: boolean;
}

interface StockMovement {
  id: string; inventory_item_id: string; movement_type: string;
  quantity: number; batch_number: string | null; notes: string | null; created_at: string;
}

interface Vendor { id: string; name: string; }
interface PurchaseOrder { id: string; order_number: string; vendor_id: string; status: string; subtotal: number; tax_amount: number; total: number; expected_delivery: string | null; notes: string | null; created_at: string; }

interface ItemForm {
  name: string; item_code: string; unit: string; current_stock: string;
  minimum_stock: string; cost_price: string; selling_price: string; category_id: string;
}

interface AdjustmentForm {
  inventory_item_id: string; quantity: string; movement_type: string; notes: string; batch_number: string;
}

const emptyItemForm: ItemForm = { name: '', item_code: '', unit: 'kg', current_stock: '0', minimum_stock: '0', cost_price: '', selling_price: '', category_id: '' };
const emptyAdjustment: AdjustmentForm = { inventory_item_id: '', quantity: '', movement_type: 'adjustment_in', notes: '', batch_number: '' };

const statusColors: Record<string, string> = { draft: 'bg-gray-100 text-gray-700', approved: 'bg-blue-100 text-blue-700', received: 'bg-green-100 text-green-700' };

export default function Inventory() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'items' | 'movements' | 'orders'>('items');
  const [showItemForm, setShowItemForm] = useState(false);
  const [showAdjustment, setShowAdjustment] = useState(false);
  const [showPOForm, setShowPOForm] = useState(false);
  const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
  const [itemForm, setItemForm] = useState<ItemForm>(emptyItemForm);
  const [adjForm, setAdjForm] = useState<AdjustmentForm>(emptyAdjustment);
  const [error, setError] = useState<string | null>(null);
  const [poForm, setPoForm] = useState({ vendor_id: '', expected_delivery: '', notes: '', items: [{ inventory_item_id: '', quantity: '', unit_price: '' }] });

  // React Query hooks
  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: queryKeys.inventory.items(),
    queryFn: () => apiClient.get('/inventory/items').then(res => res.data),
  });

  const { data: lowStock = [] } = useQuery({
    queryKey: queryKeys.inventory.lowStock(),
    queryFn: () => apiClient.get('/inventory/low-stock').then(res => res.data).catch(() => []),
  });

  const { data: vendors = [] } = useQuery({
    queryKey: ['vendors'],
    queryFn: () => apiClient.get('/vendors/').then(res => res.data).catch(() => []),
  });

  const { data: purchaseOrders = [] } = useQuery({
    queryKey: ['purchase-orders'],
    queryFn: () => apiClient.get('/purchase-orders/').then(res => res.data).catch(() => []),
  });

  // Mutations
  const saveItemMutation = useMutation({
    mutationFn: (data: { id?: string; payload: Record<string, unknown> }) =>
      data.id ? apiClient.put(`/inventory/items/${data.id}`, data.payload) : apiClient.post('/inventory/items', data.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.inventory.all });
      setShowItemForm(false);
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to save'),
  });

  const deleteItemMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/inventory/items/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.inventory.all }),
  });

  const adjustmentMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => apiClient.post('/inventory/stock-movements', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.inventory.all });
      setShowAdjustment(false);
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to save'),
  });

  const savePOMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => apiClient.post('/purchase-orders/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase-orders'] });
      setShowPOForm(false);
    },
    onError: (err: any) => setError(err.response?.data?.detail || 'Failed to create PO'),
  });

  const approvePOMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/purchase-orders/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['purchase-orders'] }),
  });

  const receivePOMutation = useMutation({
    mutationFn: (id: string) => apiClient.post(`/purchase-orders/${id}/receive`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['purchase-orders'] }),
  });

  // Handlers
  const openCreateItem = () => { setItemForm(emptyItemForm); setEditingItem(null); setShowItemForm(true); setError(null); };
  const openEditItem = (item: InventoryItem) => {
    setItemForm({ name: item.name, item_code: item.item_code || '', unit: item.unit, current_stock: String(item.current_stock), minimum_stock: String(item.minimum_stock), cost_price: String(item.cost_price), selling_price: item.selling_price ? String(item.selling_price) : '', category_id: item.category_id || '' });
    setEditingItem(item); setShowItemForm(true); setError(null);
  };

  const saveItem = () => {
    if (!itemForm.name) { setError('Name required'); return; }
    const payload = { ...itemForm, current_stock: parseFloat(itemForm.current_stock) || 0, minimum_stock: parseFloat(itemForm.minimum_stock) || 0, cost_price: parseFloat(itemForm.cost_price) || 0, selling_price: itemForm.selling_price ? parseFloat(itemForm.selling_price) : null, category_id: itemForm.category_id || null };
    saveItemMutation.mutate({ id: editingItem?.id, payload });
  };

  const saveAdjustment = () => {
    if (!adjForm.inventory_item_id || !adjForm.quantity) { setError('Item and quantity required'); return; }
    adjustmentMutation.mutate({
      inventory_item_id: adjForm.inventory_item_id, movement_type: adjForm.movement_type,
      quantity: parseFloat(adjForm.quantity), notes: adjForm.notes || null, batch_number: adjForm.batch_number || null,
    });
  };

  const savePO = () => {
    if (!poForm.vendor_id || poForm.items.length === 0) { setError('Vendor and items required'); return; }
    savePOMutation.mutate({
      vendor_id: poForm.vendor_id, branch_id: '', expected_delivery: poForm.expected_delivery || null,
      notes: poForm.notes || null,
      items: poForm.items.map(i => ({ inventory_item_id: i.inventory_item_id, quantity: parseFloat(i.quantity), unit_price: parseFloat(i.unit_price) })),
    });
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Inventory</h2>
          <p className="text-sm text-gray-500 mt-1">{items.length} items tracked</p>
        </div>
        <div className="flex gap-2">
          {tab === 'items' && <button onClick={openCreateItem} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">+ Add Item</button>}
          {tab === 'items' && <button onClick={() => { setAdjForm(emptyAdjustment); setShowAdjustment(true); setError(null); }} className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 text-sm font-medium">Stock Adjustment</button>}
          {tab === 'orders' && <button onClick={() => setShowPOForm(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">+ New PO</button>}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-4">
        {(['items', 'movements', 'orders'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} className={`pb-2 font-medium capitalize transition-colors ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            {t === 'orders' ? 'Purchase Orders' : t === 'movements' ? 'Stock Movements' : `Items (${items.length})`}
          </button>
        ))}
      </div>

      {/* Low Stock Alert */}
      {lowStock.length > 0 && tab === 'items' && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl">
          <h4 className="text-red-700 font-semibold mb-2">Low Stock Alert ({lowStock.length} items)</h4>
          <div className="flex flex-wrap gap-2">
            {lowStock.map((item: InventoryItem) => (
              <span key={item.id} className="bg-red-100 text-red-700 px-2 py-1 rounded-lg text-sm">{item.name} ({item.current_stock} {item.unit})</span>
            ))}
          </div>
        </div>
      )}

      {/* Items Table */}
      {tab === 'items' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Min</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {itemsLoading ? (
                <><TableRowSkeleton columns={7} /><TableRowSkeleton columns={7} /><TableRowSkeleton columns={7} /></>
              ) : items.length === 0 ? (
                <tr><td colSpan={7} className="px-6 py-12 text-center text-gray-400"><div className="text-4xl mb-2">📦</div><p className="text-lg font-medium">No inventory items</p><p className="text-sm mt-1">Add your first item to start tracking</p></td></tr>
              ) : items.map((item: InventoryItem) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900">{item.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{item.item_code || '-'}</td>
                  <td className="px-6 py-4 text-sm">{item.current_stock} {item.unit}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{item.minimum_stock} {item.unit}</td>
                  <td className="px-6 py-4 text-right font-semibold text-gray-900">₹{Number(item.cost_price).toFixed(2)}</td>
                  <td className="px-6 py-4">
                    {item.current_stock <= item.minimum_stock ? (
                      <span className="bg-red-100 text-red-700 px-2 py-1 rounded-full text-xs font-medium">Low</span>
                    ) : (
                      <span className="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs font-medium">OK</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => { setAdjForm({ ...emptyAdjustment, inventory_item_id: item.id }); setShowAdjustment(true); setError(null); }} className="text-orange-500 hover:text-orange-700 text-sm font-medium mr-3">Adjust</button>
                    <button onClick={() => openEditItem(item)} className="text-blue-500 hover:text-blue-700 text-sm font-medium mr-3">Edit</button>
                    <button onClick={() => { if (confirm('Delete?')) deleteItemMutation.mutate(item.id); }} className="text-red-500 hover:text-red-700 text-sm font-medium">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stock Movements */}
      {tab === 'movements' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400">No stock movements yet</td></tr>
              ) : (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400"><div className="text-4xl mb-2">📊</div><p className="text-lg font-medium">Stock movements</p><p className="text-sm mt-1">Movements will appear here after stock adjustments</p></td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Purchase Orders */}
      {tab === 'orders' && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">PO Number</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Delivery</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(purchaseOrders as PurchaseOrder[]).length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-400"><div className="text-4xl mb-2">📋</div><p className="text-lg font-medium">No purchase orders</p><p className="text-sm mt-1">Create your first PO to start procurement</p></td></tr>
              ) : (purchaseOrders as PurchaseOrder[]).map(po => (
                <tr key={po.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900">{po.order_number}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{(vendors as Vendor[]).find(v => v.id === po.vendor_id)?.name || po.vendor_id}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[po.status] || ''}`}>{po.status}</span></td>
                  <td className="px-6 py-4 text-right font-semibold text-gray-900">₹{Number(po.total).toFixed(2)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{po.expected_delivery || '-'}</td>
                  <td className="px-6 py-4 text-right">
                    {po.status === 'draft' && <button onClick={() => approvePOMutation.mutate(po.id)} className="text-blue-500 hover:text-blue-700 text-sm font-medium mr-3">Approve</button>}
                    {po.status === 'approved' && <button onClick={() => receivePOMutation.mutate(po.id)} className="text-green-500 hover:text-green-700 text-sm font-medium">Receive</button>}
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
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 className="text-lg font-bold mb-4">{editingItem ? 'Edit Item' : 'Add Inventory Item'}</h3>
            {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
            <div className="space-y-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Name *</label><input value={itemForm.name} onChange={e => setItemForm({...itemForm, name: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Code</label><input value={itemForm.item_code} onChange={e => setItemForm({...itemForm, item_code: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Unit</label><select value={itemForm.unit} onChange={e => setItemForm({...itemForm, unit: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"><option>kg</option><option>g</option><option>l</option><option>ml</option><option>pcs</option><option>box</option></select></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Current Stock</label><input type="number" value={itemForm.current_stock} onChange={e => setItemForm({...itemForm, current_stock: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Minimum Stock</label><input type="number" value={itemForm.minimum_stock} onChange={e => setItemForm({...itemForm, minimum_stock: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Cost Price</label><input type="number" value={itemForm.cost_price} onChange={e => setItemForm({...itemForm, cost_price: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Selling Price</label><input type="number" value={itemForm.selling_price} onChange={e => setItemForm({...itemForm, selling_price: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveItem} disabled={saveItemMutation.isPending} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">{saveItemMutation.isPending ? 'Saving...' : 'Save'}</button>
              <button onClick={() => setShowItemForm(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg hover:bg-gray-200 font-medium">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Stock Adjustment Modal */}
      {showAdjustment && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 className="text-lg font-bold mb-4">Stock Adjustment</h3>
            {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
            <div className="space-y-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Item *</label>
                <select value={adjForm.inventory_item_id} onChange={e => setAdjForm({...adjForm, inventory_item_id: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select item...</option>
                  {items.map((i: InventoryItem) => <option key={i.id} value={i.id}>{i.name} ({i.current_stock} {i.unit})</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select value={adjForm.movement_type} onChange={e => setAdjForm({...adjForm, movement_type: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="adjustment_in">Stock In (+)</option>
                  <option value="adjustment_out">Stock Out (-)</option>
                  <option value="waste">Waste</option>
                  <option value="return">Return</option>
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label><input type="number" value={adjForm.quantity} onChange={e => setAdjForm({...adjForm, quantity: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Batch Number</label><input value={adjForm.batch_number} onChange={e => setAdjForm({...adjForm, batch_number: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={adjForm.notes} onChange={e => setAdjForm({...adjForm, notes: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Reason for adjustment" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveAdjustment} disabled={adjustmentMutation.isPending} className="flex-1 bg-orange-500 text-white py-2.5 rounded-lg hover:bg-orange-600 disabled:opacity-50 font-medium">{adjustmentMutation.isPending ? 'Saving...' : 'Adjust Stock'}</button>
              <button onClick={() => setShowAdjustment(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg hover:bg-gray-200 font-medium">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Purchase Order Form Modal */}
      {showPOForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-auto shadow-2xl">
            <h3 className="text-lg font-bold mb-4">Create Purchase Order</h3>
            {error && <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>}
            <div className="space-y-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Vendor *</label>
                <select value={poForm.vendor_id} onChange={e => setPoForm({...poForm, vendor_id: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select vendor...</option>
                  {(vendors as Vendor[]).map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Expected Delivery</label><input type="date" value={poForm.expected_delivery} onChange={e => setPoForm({...poForm, expected_delivery: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={poForm.notes} onChange={e => setPoForm({...poForm, notes: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" /></div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Items *</label>
                {poForm.items.map((item, idx) => (
                  <div key={idx} className="flex gap-2 mb-2">
                    <select value={item.inventory_item_id} onChange={e => { const newItems = [...poForm.items]; newItems[idx].inventory_item_id = e.target.value; setPoForm({...poForm, items: newItems}) }} className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      <option value="">Item...</option>
                      {items.map((i: InventoryItem) => <option key={i.id} value={i.id}>{i.name}</option>)}
                    </select>
                    <input type="number" placeholder="Qty" value={item.quantity} onChange={e => { const newItems = [...poForm.items]; newItems[idx].quantity = e.target.value; setPoForm({...poForm, items: newItems}) }} className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    <input type="number" placeholder="Price" value={item.unit_price} onChange={e => { const newItems = [...poForm.items]; newItems[idx].unit_price = e.target.value; setPoForm({...poForm, items: newItems}) }} className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    {poForm.items.length > 1 && <button onClick={() => { setPoForm({ ...poForm, items: poForm.items.filter((_, i) => i !== idx) }) }} className="text-red-500 px-2 hover:text-red-700">✕</button>}
                  </div>
                ))}
                <button onClick={() => setPoForm({ ...poForm, items: [...poForm.items, { inventory_item_id: '', quantity: '', unit_price: '' }] })} className="text-blue-500 text-sm hover:text-blue-700 font-medium">+ Add item</button>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={savePO} disabled={savePOMutation.isPending} className="flex-1 bg-blue-600 text-white py-2.5 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium">{savePOMutation.isPending ? 'Creating...' : 'Create PO'}</button>
              <button onClick={() => setShowPOForm(false)} className="flex-1 bg-gray-100 text-gray-700 py-2.5 rounded-lg hover:bg-gray-200 font-medium">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
