import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

export default function Reports() {
  const [dailySales, setDailySales] = useState<any>(null)
  const [itemSales, setItemSales] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      const [dailyRes, itemRes] = await Promise.all([
        apiClient.get('/reports/daily-sales'),
        apiClient.get('/reports/item-wise-sales'),
      ])
      setDailySales(dailyRes.data)
      setItemSales(itemRes.data)
    } catch (err) {
      console.error('Failed to load reports', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading...</div>

  return (
    <div className="space-y-6">
      {/* Daily Sales */}
      {dailySales && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Today's Sales</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Orders</p>
              <p className="text-2xl font-bold">{dailySales.order_count}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Revenue</p>
              <p className="text-2xl font-bold">₹{Number(dailySales.total_sales).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Order</p>
              <p className="text-2xl font-bold">₹{Number(dailySales.avg_order_value).toFixed(0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Tax Collected</p>
              <p className="text-2xl font-bold">₹{Number(dailySales.total_tax).toFixed(0)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Items */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Top Selling Items</h3>
        <div className="space-y-3">
          {itemSales.slice(0, 10).map((item, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-gray-400 w-6">{i + 1}</span>
                <span className="font-medium">{item.item_name}</span>
              </div>
              <div className="text-right">
                <p className="font-semibold">₹{Number(item.total_revenue).toFixed(0)}</p>
                <p className="text-sm text-gray-500">{Number(item.total_quantity)} sold</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Payment Breakdown */}
      {dailySales?.payment_breakdown && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Payment Methods</h3>
          <div className="space-y-2">
            {dailySales.payment_breakdown.map((p: any, i: number) => (
              <div key={i} className="flex justify-between">
                <span className="capitalize">{p.method}</span>
                <span className="font-semibold">₹{Number(p.total).toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
