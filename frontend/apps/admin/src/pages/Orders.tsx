import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { TableRowSkeleton } from '../components/Skeleton'

interface Order {
  id: string
  order_number: string
  order_type: string
  status: string
  total: number
  customer_name: string
  created_at: string
}

const STATUS_FILTERS = ['all', 'pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled'] as const;

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  preparing: 'bg-orange-100 text-orange-800',
  ready: 'bg-green-100 text-green-800',
  completed: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-red-100 text-red-800',
};

const typeIcons: Record<string, string> = {
  dine_in: '🍽️',
  takeaway: '📦',
  delivery: '🚗',
  online: '🌐',
};

export default function Orders() {
  const [filter, setFilter] = useState<string>('all');
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.orders.list({ status: filter }),
    queryFn: () => {
      const params: Record<string, string> = {};
      if (filter !== 'all') params.status = filter;
      return apiClient.get('/orders/', { params }).then(res => res.data);
    },
    refetchInterval: 15_000,
  });

  const orders: Order[] = data?.data || data || [];

  const updateStatusMutation = useMutation({
    mutationFn: ({ orderId, status }: { orderId: string; status: string }) =>
      apiClient.put(`/orders/${orderId}/status`, null, { params: { new_status: status } }),

    // Optimistic update - update UI immediately before server responds
    onMutate: async ({ orderId, status }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.orders.all });

      // Snapshot previous value
      const previousOrders = queryClient.getQueryData(queryKeys.orders.list({ status: filter }));

      // Optimistically update
      queryClient.setQueryData(queryKeys.orders.list({ status: filter }), (old: any) => {
        if (!old) return old;
        const orders = old.data || old;
        return {
          ...old,
          data: orders.map((order: Order) =>
            order.id === orderId ? { ...order, status } : order
          ),
        };
      });

      return { previousOrders };
    },

    // On error, roll back
    onError: (_err, _variables, context) => {
      if (context?.previousOrders) {
        queryClient.setQueryData(queryKeys.orders.list({ status: filter }), context.previousOrders);
      }
    },

    // Always refetch after error or success
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.orders.all });
    },
  });

  const getNextStatus = (current: string): string | null => {
    const flow: Record<string, string> = {
      pending: 'confirmed',
      confirmed: 'preparing',
      preparing: 'ready',
      ready: 'completed',
    };
    return flow[current] || null;
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-red-500 text-lg">Failed to load orders</p>
        <button onClick={() => refetch()} className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Orders</h2>
          <p className="text-sm text-gray-500 mt-1">Manage and track all orders</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">{orders.length} orders</span>
          <button onClick={() => refetch()} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {STATUS_FILTERS.map(status => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm capitalize whitespace-nowrap transition-colors ${
              filter === status ? 'bg-blue-500 text-white shadow-sm' : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <>
                <TableRowSkeleton columns={7} />
                <TableRowSkeleton columns={7} />
                <TableRowSkeleton columns={7} />
                <TableRowSkeleton columns={7} />
                <TableRowSkeleton columns={7} />
              </>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center">
                  <div className="text-gray-400">
                    <div className="text-4xl mb-2">📋</div>
                    <p className="text-lg font-medium">No orders found</p>
                    <p className="text-sm mt-1">{filter !== 'all' ? `No ${filter} orders` : 'Orders will appear here'}</p>
                  </div>
                </td>
              </tr>
            ) : (
              orders.map(order => {
                const nextStatus = getNextStatus(order.status);
                return (
                  <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{order.order_number}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1.5 text-sm">
                        <span>{typeIcons[order.order_type] || '📋'}</span>
                        <span className="capitalize">{order.order_type?.replace('_', ' ')}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{order.customer_name || 'Walk-in'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${statusColors[order.status] || ''}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-gray-900">₹{Number(order.total).toFixed(2)}</td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {nextStatus && (
                        <button
                          onClick={() => updateStatusMutation.mutate({ orderId: order.id, status: nextStatus })}
                          className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                        >
                          {nextStatus === 'confirmed' ? 'Confirm' :
                           nextStatus === 'preparing' ? 'Start' :
                           nextStatus === 'ready' ? 'Ready' :
                           nextStatus === 'completed' ? 'Complete' : nextStatus}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
