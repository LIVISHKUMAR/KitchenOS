import React, { useState } from 'react'
import apiClient from '../api/client'

interface GSTSummary {
  month: string
  summary: {
    total_orders: number
    total_revenue: number
    total_tax: number
    total_cgst: number
    total_sgst: number
  }
  hsn_summary: Array<{
    hsn_code: string
    quantity: number
    taxable_value: number
    cgst: number
    sgst: number
    total: number
  }>
}

export default function GSTReports() {
  const currentMonth = new Date().toISOString().slice(0, 7)
  const [month, setMonth] = useState(currentMonth)
  const [data, setData] = useState<GSTSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadReport = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await apiClient.get('/reports/gst-summary', { params: { month } })
      setData(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load GST report')
    } finally {
      setLoading(false)
    }
  }

  const exportGSTR1 = async () => {
    try {
      const res = await apiClient.get('/reports/gstr1', { params: { month } })
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gstr1-${month}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export GSTR-1')
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">GST Reports</h3>
        <div className="flex gap-2">
          <input
            type="month"
            value={month}
            onChange={e => setMonth(e.target.value)}
            className="px-3 py-2 border rounded text-sm"
          />
          <button onClick={loadReport} disabled={loading} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm disabled:opacity-50">
            {loading ? 'Loading...' : 'Generate'}
          </button>
          {data && (
            <button onClick={exportGSTR1} className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 text-sm">
              Export GSTR-1 JSON
            </button>
          )}
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-600 rounded">{error}</div>}

      {!data && !loading && (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Select a month and click Generate to view GST summary
        </div>
      )}

      {data && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Total Orders</div>
              <div className="text-2xl font-bold">{data.summary.total_orders}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Taxable Revenue</div>
              <div className="text-2xl font-bold">₹{data.summary.total_revenue.toLocaleString()}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">Total Tax</div>
              <div className="text-2xl font-bold text-blue-600">₹{data.summary.total_tax.toFixed(2)}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">CGST (9%)</div>
              <div className="text-2xl font-bold text-green-600">₹{data.summary.total_cgst.toFixed(2)}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-500">SGST (9%)</div>
              <div className="text-2xl font-bold text-green-600">₹{data.summary.total_sgst.toFixed(2)}</div>
            </div>
          </div>

          {/* HSN Summary Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b">
              <h4 className="font-semibold">HSN-wise Summary</h4>
            </div>
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">HSN Code</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Qty</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.hsn_summary.map((hsn, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-mono">{hsn.hsn_code}</td>
                    <td className="px-6 py-4 text-gray-500 text-right">Restaurant Services</td>
                    <td className="px-6 py-4 text-right">{hsn.quantity}</td>
                    <td className="px-6 py-4 text-right">₹{hsn.taxable_value.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right">₹{hsn.cgst.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right">₹{hsn.sgst.toFixed(2)}</td>
                    <td className="px-6 py-4 text-right font-bold">₹{hsn.total.toFixed(2)}</td>
                  </tr>
                ))}
                {data.hsn_summary.length === 0 && (
                  <tr><td colSpan={7} className="px-6 py-4 text-center text-gray-500">No data for this month</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {/* GSTR-1 Info */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2">GSTR-1 Filing Notes</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>- HSN Code 996331: Restaurant and catering services</li>
              <li>- Tax rate: 5% GST (2.5% CGST + 2.5% SGST) for non-AC restaurants</li>
              <li>- Tax rate: 18% GST (9% CGST + 9% SGST) for AC restaurants</li>
              <li>- Export the JSON file and upload to the GST portal</li>
              <li>- Ensure your GSTIN is configured in Settings</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
