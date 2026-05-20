import React, { useState } from 'react'
import apiClient from '../api/client'

interface ReportConfig {
  name: string
  type: 'sales' | 'inventory' | 'customer' | 'staff'
  dateRange: 'today' | 'week' | 'month' | 'custom'
  startDate: string
  endDate: string
  metrics: string[]
  groupBy: string
  filters: Record<string, string>
}

const METRICS: Record<string, string[]> = {
  sales: ['total_revenue', 'order_count', 'avg_order_value', 'tax_collected', 'discount_given', 'refund_amount'],
  inventory: ['stock_level', 'consumption', 'waste', 'cost_value', 'reorder_alerts'],
  customer: ['total_customers', 'new_customers', 'repeat_rate', 'avg_spend', 'loyalty_points'],
  staff: ['orders_handled', 'revenue_generated', 'avg_order_time', 'attendance'],
}

const GROUP_OPTIONS = ['day', 'week', 'month', 'category', 'item', 'payment_method', 'branch']

export default function ReportBuilder() {
  const [config, setConfig] = useState<ReportConfig>({
    name: '',
    type: 'sales',
    dateRange: 'month',
    startDate: '',
    endDate: '',
    metrics: ['total_revenue', 'order_count'],
    groupBy: 'day',
    filters: {},
  })
  const [reportData, setReportData] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [savedReports, setSavedReports] = useState<Array<{ name: string; config: ReportConfig }>>(() => {
    try {
      return JSON.parse(localStorage.getItem('kitchenos_saved_reports') || '[]')
    } catch { return [] }
  })

  const toggleMetric = (metric: string) => {
    setConfig({
      ...config,
      metrics: config.metrics.includes(metric)
        ? config.metrics.filter(m => m !== metric)
        : [...config.metrics, metric],
    })
  }

  const generateReport = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {
        type: config.type,
        period: config.dateRange,
        group_by: config.groupBy,
        metrics: config.metrics.join(','),
      }
      if (config.dateRange === 'custom') {
        params.start_date = config.startDate
        params.end_date = config.endDate
      }
      const res = await apiClient.get('/reports/custom', { params }).catch(() => ({ data: [] }))
      setReportData(Array.isArray(res.data) ? res.data : [])
    } catch {
      setReportData([])
    } finally {
      setLoading(false)
    }
  }

  const saveReport = () => {
    if (!config.name) return
    const updated = [...savedReports, { name: config.name, config }]
    setSavedReports(updated)
    localStorage.setItem('kitchenos_saved_reports', JSON.stringify(updated))
  }

  const loadReport = (saved: { name: string; config: ReportConfig }) => {
    setConfig(saved.config)
  }

  const exportCSV = () => {
    if (!reportData || reportData.length === 0) return
    const headers = Object.keys(reportData[0]).join(',')
    const rows = reportData.map(row => Object.values(row).join(',')).join('\n')
    const blob = new Blob([headers + '\n' + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${config.name || 'report'}-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Custom Report Builder</h3>
        <div className="flex gap-2">
          {reportData && (
            <button onClick={exportCSV} className="bg-gray-100 text-gray-700 px-4 py-2 rounded hover:bg-gray-200 text-sm">
              Export CSV
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-6">
        {/* Config Panel */}
        <div className="w-80 space-y-4">
          {/* Report Type */}
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold text-sm mb-3">Report Type</h4>
            <div className="grid grid-cols-2 gap-2">
              {(['sales', 'inventory', 'customer', 'staff'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setConfig({ ...config, type: t, metrics: METRICS[t].slice(0, 2) })}
                  className={`p-2 rounded text-sm capitalize ${config.type === t ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                >{t}</button>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold text-sm mb-3">Date Range</h4>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {(['today', 'week', 'month', 'custom'] as const).map(r => (
                <button
                  key={r}
                  onClick={() => setConfig({ ...config, dateRange: r })}
                  className={`p-2 rounded text-sm capitalize ${config.dateRange === r ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                >{r === 'custom' ? 'Custom' : r}</button>
              ))}
            </div>
            {config.dateRange === 'custom' && (
              <div className="space-y-2">
                <input type="date" value={config.startDate} onChange={e => setConfig({ ...config, startDate: e.target.value })} className="w-full px-3 py-2 border rounded text-sm" />
                <input type="date" value={config.endDate} onChange={e => setConfig({ ...config, endDate: e.target.value })} className="w-full px-3 py-2 border rounded text-sm" />
              </div>
            )}
          </div>

          {/* Metrics */}
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold text-sm mb-3">Metrics</h4>
            <div className="space-y-1">
              {METRICS[config.type].map(m => (
                <label key={m} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={config.metrics.includes(m)} onChange={() => toggleMetric(m)} />
                  <span className="capitalize">{m.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Group By */}
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold text-sm mb-3">Group By</h4>
            <select value={config.groupBy} onChange={e => setConfig({ ...config, groupBy: e.target.value })} className="w-full px-3 py-2 border rounded text-sm">
              {GROUP_OPTIONS.map(g => <option key={g} value={g} className="capitalize">{g.replace(/_/g, ' ')}</option>)}
            </select>
          </div>

          {/* Save & Generate */}
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Report name"
                value={config.name}
                onChange={e => setConfig({ ...config, name: e.target.value })}
                className="flex-1 px-3 py-2 border rounded text-sm"
              />
              <button onClick={saveReport} disabled={!config.name} className="px-3 py-2 bg-gray-100 rounded text-sm hover:bg-gray-200 disabled:opacity-50">Save</button>
            </div>
            <button
              onClick={generateReport}
              disabled={loading}
              className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50 font-medium"
            >
              {loading ? 'Generating...' : 'Generate Report'}
            </button>
          </div>

          {/* Saved Reports */}
          {savedReports.length > 0 && (
            <div className="bg-white rounded-lg shadow p-4">
              <h4 className="font-semibold text-sm mb-3">Saved Reports</h4>
              <div className="space-y-1">
                {savedReports.map((r, i) => (
                  <button
                    key={i}
                    onClick={() => loadReport(r)}
                    className="w-full text-left p-2 rounded hover:bg-gray-50 text-sm"
                  >
                    {r.name}
                    <span className="text-gray-400 ml-2 text-xs capitalize">({r.config.type})</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="flex-1">
          {!reportData ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              Configure your report and click Generate
            </div>
          ) : reportData.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              No data found for the selected criteria
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b flex justify-between items-center">
                <h4 className="font-semibold">{config.name || `${config.type} Report`}</h4>
                <span className="text-sm text-gray-500">{reportData.length} rows</span>
              </div>
              <div className="overflow-auto max-h-[600px]">
                <table className="w-full">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      {Object.keys(reportData[0]).map(key => (
                        <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          {key.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {reportData.map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        {Object.values(row).map((val, j) => (
                          <td key={j} className="px-6 py-4 text-sm">
                            {typeof val === 'number' ? val.toLocaleString() : String(val || '-')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
