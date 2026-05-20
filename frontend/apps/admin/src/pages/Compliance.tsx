import React, { useState } from 'react'

interface ComplianceItem {
  id: string
  name: string
  category: string
  status: 'compliant' | 'pending' | 'non_compliant' | 'not_applicable'
  description: string
  dueDate: string | null
}

export default function Compliance() {
  const [tab, setTab] = useState<'checklist' | 'fssai' | 'currency' | 'retention'>('checklist')

  const [complianceItems] = useState<ComplianceItem[]>([
    { id: '1', name: 'GST Registration', category: 'Tax', status: 'compliant', description: 'GSTIN registered and active', dueDate: null },
    { id: '2', name: 'FSSAI License', category: 'Food Safety', status: 'pending', description: 'Food Safety and Standards Authority license', dueDate: '2026-06-30' },
    { id: '3', name: 'E-Invoicing', category: 'Tax', status: 'compliant', description: 'IRN generation for invoices >₹5Cr', dueDate: null },
    { id: '4', name: 'Fire Safety Certificate', category: 'Safety', status: 'pending', description: 'Fire NOC from local authority', dueDate: '2026-07-15' },
    { id: '5', name: 'Trade License', category: 'Legal', status: 'compliant', description: 'Municipal trade license', dueDate: null },
    { id: '6', name: 'Health License', category: 'Health', status: 'compliant', description: 'Health department clearance', dueDate: null },
    { id: '7', name: 'Music License', category: 'Legal', status: 'not_applicable', description: 'IPRS/PPL license for playing music', dueDate: null },
    { id: '8', name: 'Liquor License', category: 'Legal', status: 'not_applicable', description: 'License for serving alcohol', dueDate: null },
    { id: '9', name: 'Data Protection', category: 'Privacy', status: 'compliant', description: 'DPDPA compliance for customer data', dueDate: null },
    { id: '10', name: 'PCI-DSS', category: 'Security', status: 'compliant', description: 'Payment card data security (via Razorpay)', dueDate: null },
  ])

  const [fssaiForm, setFssaiForm] = useState({
    license_number: '',
    expiry_date: '',
    category: 'restaurant',
    annual_turnover: '',
    address: '',
  })

  const [currency, setCurrency] = useState({
    base_currency: 'INR',
    display_currencies: ['INR'],
    exchange_rate_source: 'manual',
  })

  const [retention, setRetention] = useState({
    orders: '365',
    audit_logs: '730',
    customer_data: '1095',
    financial_records: '2555',
    backups: '30',
  })

  const statusColors: Record<string, string> = {
    compliant: 'bg-green-100 text-green-700',
    pending: 'bg-yellow-100 text-yellow-700',
    non_compliant: 'bg-red-100 text-red-700',
    not_applicable: 'bg-gray-100 text-gray-500',
  }

  const statusIcons: Record<string, string> = {
    compliant: '✅',
    pending: '⏳',
    non_compliant: '❌',
    not_applicable: '➖',
  }

  const compliantCount = complianceItems.filter(i => i.status === 'compliant').length
  const pendingCount = complianceItems.filter(i => i.status === 'pending').length
  const totalCount = complianceItems.filter(i => i.status !== 'not_applicable').length

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Compliance & Settings</h3>
        <div className="flex gap-4">
          {(['checklist', 'fssai', 'currency', 'retention'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`pb-2 font-medium capitalize ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>{t === 'fssai' ? 'FSSAI' : t}</button>
          ))}
        </div>
      </div>

      {/* Compliance Checklist */}
      {tab === 'checklist' && (
        <div>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">{compliantCount}/{totalCount}</div>
              <div className="text-sm text-green-700">Compliant</div>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
              <div className="text-sm text-yellow-700">Pending</div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">{Math.round(compliantCount / totalCount * 100)}%</div>
              <div className="text-sm text-blue-700">Compliance Score</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Item</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Due Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {complianceItems.map(item => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium">{item.name}</td>
                    <td className="px-6 py-4 text-gray-500">{item.category}</td>
                    <td className="px-6 py-4 text-gray-500 text-sm">{item.description}</td>
                    <td className="px-6 py-4 text-gray-500">{item.dueDate || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${statusColors[item.status]}`}>
                        {statusIcons[item.status]} {item.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FSSAI */}
      {tab === 'fssai' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">FSSAI License Management</h4>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">FSSAI License Number</label><input value={fssaiForm.license_number} onChange={e => setFssaiForm({...fssaiForm, license_number: e.target.value})} className="w-full px-3 py-2 border rounded" placeholder="e.g. 12345678901234" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label><input type="date" value={fssaiForm.expiry_date} onChange={e => setFssaiForm({...fssaiForm, expiry_date: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Category</label><select value={fssaiForm.category} onChange={e => setFssaiForm({...fssaiForm, category: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="restaurant">Restaurant</option><option value="cloud_kitchen">Cloud Kitchen</option><option value="catering">Catering</option><option value="food_chain">Food Chain</option></select></div>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Annual Turnover</label><select value={fssaiForm.annual_turnover} onChange={e => setFssaiForm({...fssaiForm, annual_turnover: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="">Select...</option><option value="below_12l">Below ₹12 Lakhs</option><option value="12l_20cr">₹12L - ₹20 Crore</option><option value="above_20cr">Above ₹20 Crore</option></select></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Business Address</label><textarea value={fssaiForm.address} onChange={e => setFssaiForm({...fssaiForm, address: e.target.value})} className="w-full px-3 py-2 border rounded" rows={2} /></div>
              <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">Save FSSAI Details</button>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-yellow-800 mb-2">FSSAI Compliance Notes</h4>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>- FSSAI license must be displayed at the premises</li>
              <li>- Renewal must be done before expiry (30 days minimum)</li>
              <li>- Annual return must be filed by May 31st</li>
              <li>- Food safety audit may be conducted by FSSAI officers</li>
              <li>- Maintain hygiene rating as per FSSAI guidelines</li>
            </ul>
          </div>
        </div>
      )}

      {/* Multi-Currency */}
      {tab === 'currency' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Currency Configuration</h4>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Base Currency</label><select value={currency.base_currency} onChange={e => setCurrency({...currency, base_currency: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="INR">INR - Indian Rupee (₹)</option><option value="USD">USD - US Dollar ($)</option><option value="EUR">EUR - Euro (€)</option><option value="GBP">GBP - British Pound (£)</option><option value="AED">AED - UAE Dirham (د.إ)</option></select></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Display Currencies</label><div className="flex flex-wrap gap-2">{['INR', 'USD', 'EUR', 'GBP', 'AED'].map(c => (<label key={c} className="flex items-center gap-2"><input type="checkbox" checked={currency.display_currencies.includes(c)} onChange={e => { if (e.target.checked) setCurrency({...currency, display_currencies: [...currency.display_currencies, c]}); else setCurrency({...currency, display_currencies: currency.display_currencies.filter(d => d !== c)}) }} /><span>{c}</span></label>))}</div></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Exchange Rate Source</label><select value={currency.exchange_rate_source} onChange={e => setCurrency({...currency, exchange_rate_source: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="manual">Manual</option><option value="auto">Auto (API)</option></select></div>
              <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">Save Currency Settings</button>
            </div>
          </div>
        </div>
      )}

      {/* Data Retention */}
      {tab === 'retention' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Data Retention Policies</h4>
            <p className="text-sm text-gray-500 mb-4">Configure how long different types of data are retained before archival.</p>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <div><div className="font-medium">Orders</div><div className="text-sm text-gray-500">Order records and line items</div></div>
                <select value={retention.orders} onChange={e => setRetention({...retention, orders: e.target.value})} className="px-3 py-2 border rounded text-sm"><option value="90">90 days</option><option value="180">6 months</option><option value="365">1 year</option><option value="730">2 years</option><option value="1095">3 years</option><option value="2555">7 years</option></select>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div><div className="font-medium">Audit Logs</div><div className="text-sm text-gray-500">System audit trail</div></div>
                <select value={retention.audit_logs} onChange={e => setRetention({...retention, audit_logs: e.target.value})} className="px-3 py-2 border rounded text-sm"><option value="365">1 year</option><option value="730">2 years</option><option value="1095">3 years</option><option value="2555">7 years</option></select>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div><div className="font-medium">Customer Data</div><div className="text-sm text-gray-500">PII and preferences</div></div>
                <select value={retention.customer_data} onChange={e => setRetention({...retention, customer_data: e.target.value})} className="px-3 py-2 border rounded text-sm"><option value="365">1 year</option><option value="730">2 years</option><option value="1095">3 years</option><option value="2555">7 years</option><option value="0">Indefinite</option></select>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div><div className="font-medium">Financial Records</div><div className="text-sm text-gray-500">Invoices, payments, GST</div></div>
                <select value={retention.financial_records} onChange={e => setRetention({...retention, financial_records: e.target.value})} className="px-3 py-2 border rounded text-sm"><option value="1095">3 years</option><option value="1825">5 years</option><option value="2555">7 years</option><option value="3650">10 years</option></select>
              </div>
              <div className="flex justify-between items-center py-2">
                <div><div className="font-medium">Backups</div><div className="text-sm text-gray-500">Database backups</div></div>
                <select value={retention.backups} onChange={e => setRetention({...retention, backups: e.target.value})} className="px-3 py-2 border rounded text-sm"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option><option value="365">1 year</option></select>
              </div>
            </div>
            <button className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">Save Retention Policies</button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2">DPDPA Compliance Notes</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>- Digital Personal Data Protection Act (DPDPA) 2023 applies to all customer data</li>
              <li>- Customer consent must be obtained before data collection</li>
              <li>- Customers have the right to access, correct, and delete their data</li>
              <li>- Data breach must be reported within 72 hours</li>
              <li>- Financial records must be retained as per IT Act requirements</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
