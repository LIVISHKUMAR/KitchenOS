import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { queryKeys } from '../lib/queryClient'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

export default function Reports() {
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('today');

  const { data: dailySales, isLoading: dailyLoading } = useQuery({
    queryKey: queryKeys.reports.dailySales(period),
    queryFn: () => apiClient.get('/reports/daily-sales', { params: { period } }).then(res => res.data),
    refetchInterval: 30_000,
  });

  const { data: itemSales = [], isLoading: itemsLoading } = useQuery({
    queryKey: queryKeys.reports.itemSales(),
    queryFn: () => apiClient.get('/reports/item-wise-sales').then(res => res.data),
  });

  const { data: hourlySales = [] } = useQuery({
    queryKey: queryKeys.reports.hourlySales(period),
    queryFn: () => apiClient.get('/reports/hourly-sales', { params: { period } }).then(res => res.data).catch(() => []),
  });

  const exportCSV = () => {
    if (!itemSales.length) return;
    const headers = 'Item Name,Revenue,Quantity\n';
    const rows = itemSales.map((i: any) => `${i.item_name},${i.total_revenue},${i.total_quantity}`).join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sales-report-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isLoading = dailyLoading || itemsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Reports & Analytics</h2>
          <p className="text-sm text-gray-500 mt-1">Sales performance and insights</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex bg-gray-100 rounded-lg p-1">
            {(['today', 'week', 'month'] as const).map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-sm rounded-md capitalize transition-colors ${
                  period === p ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <button onClick={exportCSV} className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm hover:bg-gray-50 transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            Export CSV
          </button>
        </div>
      </div>

      {/* Daily Sales Stats */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="h-3 bg-gray-200 rounded w-20 mb-2 animate-pulse" />
              <div className="h-8 bg-gray-200 rounded w-24 animate-pulse" />
            </div>
          ))}
        </div>
      ) : dailySales ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Orders" value={dailySales.order_count} icon="📋" color="blue" />
          <StatCard label="Revenue" value={`₹${Number(dailySales.total_sales).toLocaleString()}`} icon="💰" color="green" />
          <StatCard label="Avg Order" value={`₹${Number(dailySales.avg_order_value).toFixed(0)}`} icon="📊" color="purple" />
          <StatCard label="Tax Collected" value={`₹${Number(dailySales.total_tax).toFixed(0)}`} icon="🧾" color="orange" />
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Items Bar Chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Top Selling Items</h4>
          {itemSales.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={itemSales.slice(0, 8)} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tickFormatter={v => `₹${v}`} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="item_name" width={80} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`₹${v.toFixed(0)}`, 'Revenue']} />
                <Bar dataKey="total_revenue" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">📊</div>
                <p>No sales data yet</p>
              </div>
            </div>
          )}
        </div>

        {/* Payment Methods Pie Chart */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Payment Methods</h4>
          {dailySales?.payment_breakdown?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dailySales.payment_breakdown}
                  dataKey="total"
                  nameKey="method"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ method, percent }) => `${method} ${(percent * 100).toFixed(0)}%`}
                >
                  {dailySales.payment_breakdown.map((_: any, i: number) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => [`₹${v.toFixed(0)}`, 'Amount']} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              <div className="text-center">
                <div className="text-4xl mb-2">💳</div>
                <p>No payment data yet</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Hourly Sales Chart */}
      {hourlySales.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Hourly Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={hourlySales}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="orders" fill="#10B981" name="Orders" radius={[4, 4, 0, 0]} />
              <Bar dataKey="revenue" fill="#3B82F6" name="Revenue (₹)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Item Sales Table */}
      <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h4 className="font-semibold text-gray-900">Item-wise Sales</h4>
          <span className="text-sm text-gray-500">{itemSales.length} items</span>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Revenue</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty Sold</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Price</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {itemSales.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                  <div className="text-4xl mb-2">📋</div>
                  <p className="text-lg font-medium">No sales data</p>
                  <p className="text-sm mt-1">Sales data will appear after orders are completed</p>
                </td>
              </tr>
            ) : (
              itemSales.map((item: any, i: number) => (
                <tr key={i} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-3 text-sm text-gray-400">{i + 1}</td>
                  <td className="px-6 py-3 font-medium text-gray-900">{item.item_name}</td>
                  <td className="px-6 py-3 text-right font-semibold text-gray-900">₹{Number(item.total_revenue).toLocaleString()}</td>
                  <td className="px-6 py-3 text-right text-sm text-gray-600">{Number(item.total_quantity)}</td>
                  <td className="px-6 py-3 text-right text-sm text-gray-500">
                    ₹{Number(item.total_quantity) > 0 ? (Number(item.total_revenue) / Number(item.total_quantity)).toFixed(0) : 0}
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

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  const colorStyles: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorStyles[color]} flex items-center justify-center text-xl`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
