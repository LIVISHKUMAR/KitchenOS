import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface Customer {
  id: string
  name: string
  phone: string
  email: string | null
  loyalty_points: number
  wallet_balance: number
  total_orders: number
  total_spent: number
  membership_tier: string | null
  customer_type: string
}

interface LoyaltyTransaction {
  id: string
  transaction_type: string
  points: number
  reason: string | null
  created_at: string
}

export default function Loyalty() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [transactions, setTransactions] = useState<LoyaltyTransaction[]>([])
  const [showAddPoints, setShowAddPoints] = useState(false)
  const [addPointsForm, setAddPointsForm] = useState({ points: '', reason: '' })

  useEffect(() => { loadCustomers() }, [])

  const loadCustomers = async () => {
    try {
      const res = await apiClient.get('/customers/')
      setCustomers(res.data)
    } catch (err) {
      console.error('Failed to load customers', err)
    } finally {
      setLoading(false)
    }
  }

  const loadTransactions = async (customerId: string) => {
    try {
      const res = await apiClient.get(`/loyalty/history/${customerId}`)
      setTransactions(res.data)
    } catch {
      setTransactions([])
    }
  }

  const selectCustomer = (customer: Customer) => {
    setSelectedCustomer(customer)
    loadTransactions(customer.id)
  }

  const addPoints = async () => {
    if (!selectedCustomer || !addPointsForm.points) return
    try {
      await apiClient.post(`/loyalty/earn/${selectedCustomer.id}`, null, {
        params: { order_id: 'manual', order_total: parseFloat(addPointsForm.points) * 0.1 }
      })
      setShowAddPoints(false)
      setAddPointsForm({ points: '', reason: '' })
      loadCustomers()
      loadTransactions(selectedCustomer.id)
    } catch { /* silent */ }
  }

  const getTierColor = (tier: string | null) => {
    switch (tier) {
      case 'platinum': return 'bg-purple-100 text-purple-700'
      case 'gold': return 'bg-yellow-100 text-yellow-700'
      case 'silver': return 'bg-gray-100 text-gray-700'
      default: return 'bg-blue-100 text-blue-700'
    }
  }

  const filtered = customers.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.phone.includes(search) ||
    (c.email && c.email.toLowerCase().includes(search.toLowerCase()))
  )

  // Stats
  const totalPoints = customers.reduce((s, c) => s + c.loyalty_points, 0)
  const totalCustomers = customers.length
  const avgSpend = customers.length > 0 ? customers.reduce((s, c) => s + c.total_spent, 0) / customers.length : 0

  if (loading) return <div className="p-6 text-gray-500">Loading loyalty data...</div>

  return (
    <div>
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Members</div>
          <div className="text-2xl font-bold">{totalCustomers}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Points</div>
          <div className="text-2xl font-bold text-blue-600">{totalPoints.toLocaleString()}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Avg Spend</div>
          <div className="text-2xl font-bold text-green-600">₹{avgSpend.toFixed(0)}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Top Tier</div>
          <div className="text-2xl font-bold text-purple-600">{customers.filter(c => c.membership_tier === 'platinum').length}</div>
        </div>
      </div>

      <div className="flex gap-6">
        {/* Customer List */}
        <div className="flex-1">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <input
                type="text"
                placeholder="Search by name, phone, or email..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              />
            </div>
            <div className="max-h-[600px] overflow-auto">
              {filtered.length === 0 ? (
                <div className="p-4 text-center text-gray-500">No customers found</div>
              ) : filtered.map(c => (
                <div
                  key={c.id}
                  onClick={() => selectCustomer(c)}
                  className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${selectedCustomer?.id === c.id ? 'bg-blue-50' : ''}`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="font-medium">{c.name}</div>
                      <div className="text-sm text-gray-500">{c.phone}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-blue-600">{c.loyalty_points} pts</div>
                      {c.membership_tier && (
                        <span className={`text-xs px-2 py-0.5 rounded ${getTierColor(c.membership_tier)}`}>
                          {c.membership_tier}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Customer Detail */}
        <div className="w-96">
          {selectedCustomer ? (
            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h3 className="font-bold text-lg">{selectedCustomer.name}</h3>
                <div className="text-sm text-gray-500">{selectedCustomer.phone}</div>
                {selectedCustomer.email && <div className="text-sm text-gray-500">{selectedCustomer.email}</div>}
              </div>
              <div className="p-4 grid grid-cols-2 gap-3 border-b">
                <div>
                  <div className="text-xs text-gray-500">Points</div>
                  <div className="text-xl font-bold text-blue-600">{selectedCustomer.loyalty_points}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Wallet</div>
                  <div className="text-xl font-bold text-green-600">₹{Number(selectedCustomer.wallet_balance).toFixed(0)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Orders</div>
                  <div className="font-bold">{selectedCustomer.total_orders}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Total Spent</div>
                  <div className="font-bold">₹{Number(selectedCustomer.total_spent).toFixed(0)}</div>
                </div>
              </div>
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-semibold text-sm">Transaction History</h4>
                  <button onClick={() => setShowAddPoints(true)} className="text-blue-500 text-sm hover:text-blue-700">+ Add Points</button>
                </div>
                <div className="max-h-60 overflow-auto space-y-2">
                  {transactions.length === 0 ? (
                    <div className="text-center text-gray-500 text-sm py-4">No transactions</div>
                  ) : transactions.map(t => (
                    <div key={t.id} className="flex justify-between items-center py-2 border-b text-sm">
                      <div>
                        <span className={`mr-2 ${t.transaction_type === 'earn' ? 'text-green-500' : 'text-red-500'}`}>
                          {t.transaction_type === 'earn' ? '+' : '-'}{t.points}
                        </span>
                        <span className="text-gray-500">{t.reason || t.transaction_type}</span>
                      </div>
                      <span className="text-xs text-gray-400">{new Date(t.created_at).toLocaleDateString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              Select a customer to view loyalty details
            </div>
          )}
        </div>
      </div>

      {/* Add Points Modal */}
      {showAddPoints && selectedCustomer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Add Points to {selectedCustomer.name}</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Points</label><input type="number" value={addPointsForm.points} onChange={e => setAddPointsForm({...addPointsForm, points: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Reason</label><input value={addPointsForm.reason} onChange={e => setAddPointsForm({...addPointsForm, reason: e.target.value})} className="w-full px-3 py-2 border rounded" placeholder="e.g. Bonus, Referral" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={addPoints} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600">Add Points</button>
              <button onClick={() => setShowAddPoints(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
