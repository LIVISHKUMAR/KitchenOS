import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { TableRowSkeleton } from '../components/Skeleton'

interface Customer {
  id: string
  name: string
  email: string | null
  phone: string
  loyalty_points: number
  wallet_balance: number
  total_orders: number
  total_spent: number
  customer_type: string
  membership_tier: string | null
}

const tierColors: Record<string, string> = {
  platinum: 'bg-purple-100 text-purple-700',
  gold: 'bg-yellow-100 text-yellow-700',
  silver: 'bg-gray-100 text-gray-700',
};

export default function Customers() {
  const [search, setSearch] = useState('');

  const { data: customers = [], isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.customers.list(),
    queryFn: () => apiClient.get('/customers/').then(res => res.data),
    staleTime: 30_000,
  });

  const filtered = customers.filter((c: Customer) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.phone.includes(search) ||
    (c.email && c.email.toLowerCase().includes(search.toLowerCase()))
  );

  // Stats
  const totalSpent = customers.reduce((s: number, c: Customer) => s + Number(c.total_spent), 0);
  const totalLoyalty = customers.reduce((s: number, c: Customer) => s + c.loyalty_points, 0);
  const avgSpend = customers.length > 0 ? totalSpent / customers.length : 0;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-500">Failed to load customers</p>
        <button onClick={() => refetch()} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">Retry</button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Customers</h2>
          <p className="text-sm text-gray-500 mt-1">{customers.length} customers registered</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <p className="text-sm text-gray-500">Total Customers</p>
          <p className="text-2xl font-bold text-gray-900">{customers.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <p className="text-sm text-gray-500">Total Revenue</p>
          <p className="text-2xl font-bold text-green-600">₹{totalSpent.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-4">
          <p className="text-sm text-gray-500">Avg Spend</p>
          <p className="text-2xl font-bold text-gray-900">₹{avgSpend.toFixed(0)}</p>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by name, phone, or email..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full max-w-md px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Customers Table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orders</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Spent</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Loyalty</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <>
                <TableRowSkeleton columns={6} />
                <TableRowSkeleton columns={6} />
                <TableRowSkeleton columns={6} />
              </>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                  <div className="text-4xl mb-2">👥</div>
                  <p className="text-lg font-medium">No customers found</p>
                  <p className="text-sm mt-1">{search ? 'Try a different search' : 'Customers will appear after their first order'}</p>
                </td>
              </tr>
            ) : (
              filtered.map((c: Customer) => (
                <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{c.name}</div>
                    {c.email && <div className="text-xs text-gray-500">{c.email}</div>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{c.phone}</td>
                  <td className="px-6 py-4 text-right text-sm">{c.total_orders}</td>
                  <td className="px-6 py-4 text-right font-semibold text-gray-900">₹{Number(c.total_spent).toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">
                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs font-medium">
                      {c.loyalty_points} pts
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {c.membership_tier ? (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${tierColors[c.membership_tier] || 'bg-gray-100 text-gray-700'}`}>
                        {c.membership_tier}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
