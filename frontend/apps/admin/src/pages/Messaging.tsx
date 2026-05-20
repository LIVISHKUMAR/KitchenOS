import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface Template {
  id: string
  name: string
  channel: string
  event: string
  subject: string
  body: string
}

interface NotificationLog {
  id: string
  channel: string
  to: string
  subject: string
  body: string
  status: string
  created_at: string
}

interface Campaign {
  id: string
  name: string
  channel: string
  message: string
  audience: string
  status: string
  sent_count: number
  created_at: string
}

export default function Messaging() {
  const [tab, setTab] = useState<'campaigns' | 'templates' | 'logs' | 'config'>('campaigns')
  const [templates, setTemplates] = useState<Template[]>([])
  const [logs, setLogs] = useState<NotificationLog[]>([])
  const [loading, setLoading] = useState(true)
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [showCampaignForm, setShowCampaignForm] = useState(false)
  const [templateForm, setTemplateForm] = useState({ name: '', channel: 'whatsapp', event: 'order_confirmation', subject: '', body: '' })
  const [campaignForm, setCampaignForm] = useState({ name: '', channel: 'whatsapp', message: '', audience: 'all' })
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [tplRes, logRes] = await Promise.all([
        apiClient.get('/notifications/templates').catch(() => ({ data: [] })),
        apiClient.get('/notifications/logs').catch(() => ({ data: [] })),
      ])
      setTemplates(tplRes.data)
      setLogs(logRes.data)
    } catch (err) {
      console.error('Failed to load', err)
    } finally {
      setLoading(false)
    }
  }

  const saveTemplate = async () => {
    if (!templateForm.name || !templateForm.body) { setError('Name and body required'); return }
    setSending(true); setError(null)
    try {
      await apiClient.post('/notifications/templates', templateForm)
      setShowTemplateForm(false)
      setTemplateForm({ name: '', channel: 'whatsapp', event: 'order_confirmation', subject: '', body: '' })
      loadData()
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to save') } finally { setSending(false) }
  }

  const sendCampaign = async () => {
    if (!campaignForm.message) { setError('Message required'); return }
    setSending(true); setError(null)
    try {
      // In production, this would send to all customers in the audience
      await apiClient.post('/whatsapp/send', { to: 'broadcast', message: campaignForm.message })
      setShowCampaignForm(false)
      setCampaignForm({ name: '', channel: 'whatsapp', message: '', audience: 'all' })
    } catch (err: any) { setError(err.response?.data?.detail || 'Failed to send') } finally { setSending(false) }
  }

  const channelColors: Record<string, string> = { whatsapp: 'bg-green-100 text-green-700', sms: 'bg-blue-100 text-blue-700', email: 'bg-purple-100 text-purple-700', push: 'bg-orange-100 text-orange-700' }

  if (loading) return <div className="p-6 text-gray-500">Loading messaging...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          {(['campaigns', 'templates', 'logs', 'config'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`pb-2 font-medium capitalize ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>{t}</button>
          ))}
        </div>
        <div className="flex gap-2">
          {tab === 'templates' && <button onClick={() => setShowTemplateForm(true)} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">+ Add Template</button>}
          {tab === 'campaigns' && <button onClick={() => setShowCampaignForm(true)} className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 text-sm">+ New Campaign</button>}
        </div>
      </div>

      {/* Campaigns */}
      {tab === 'campaigns' && (
        <div className="space-y-4">
          {/* Quick Actions */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md" onClick={() => { setCampaignForm({ name: 'Birthday Offers', channel: 'whatsapp', message: 'Happy Birthday! 🎂 Enjoy 15% off your next order. Use code BDAY15.', audience: 'birthday' }); setShowCampaignForm(true) }}>
              <div className="text-2xl mb-2">🎂</div>
              <div className="font-semibold">Birthday Campaign</div>
              <div className="text-sm text-gray-500">Send birthday wishes with discount</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md" onClick={() => { setCampaignForm({ name: 'Win Back', channel: 'whatsapp', message: 'We miss you! It\'s been a while since your last visit. Come back and enjoy 10% off!', audience: 'lapsed' }); setShowCampaignForm(true) }}>
              <div className="text-2xl mb-2">💝</div>
              <div className="font-semibold">Win Back Campaign</div>
              <div className="text-sm text-gray-500">Re-engage lapsed customers</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6 cursor-pointer hover:shadow-md" onClick={() => { setCampaignForm({ name: 'New Menu', channel: 'whatsapp', message: 'Exciting news! We\'ve added new items to our menu. Come try them today!', audience: 'all' }); setShowCampaignForm(true) }}>
              <div className="text-2xl mb-2">🍽️</div>
              <div className="font-semibold">New Menu Alert</div>
              <div className="text-sm text-gray-500">Announce new menu items</div>
            </div>
          </div>

          {/* Recent Campaigns */}
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Recent Campaigns</h4>
            <div className="text-center text-gray-500 py-8">No campaigns sent yet. Create your first campaign above.</div>
          </div>
        </div>
      )}

      {/* Templates */}
      {tab === 'templates' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Channel</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Body</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {templates.length === 0 ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No templates. Create your first template.</td></tr>
              ) : templates.map(t => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{t.name}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${channelColors[t.channel] || ''}`}>{t.channel}</span></td>
                  <td className="px-6 py-4 text-gray-500">{t.event}</td>
                  <td className="px-6 py-4 text-gray-500 truncate max-w-xs">{t.body}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Logs */}
      {tab === 'logs' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Channel</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Message</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {logs.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">No notification logs yet</td></tr>
              ) : logs.map(l => (
                <tr key={l.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${channelColors[l.channel] || ''}`}>{l.channel}</span></td>
                  <td className="px-6 py-4">{l.to}</td>
                  <td className="px-6 py-4 text-gray-500 truncate max-w-xs">{l.body}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${l.status === 'sent' ? 'bg-green-100 text-green-700' : l.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'}`}>{l.status}</span></td>
                  <td className="px-6 py-4 text-gray-500">{new Date(l.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Config */}
      {tab === 'config' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">WhatsApp Business API</h4>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">API Token</label><input type="password" className="w-full px-3 py-2 border rounded" placeholder="Enter WhatsApp API token" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Phone Number ID</label><input className="w-full px-3 py-2 border rounded" placeholder="Enter phone number ID" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Business Account ID</label><input className="w-full px-3 py-2 border rounded" placeholder="Enter business account ID" /></div>
              <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 text-sm">Save WhatsApp Config</button>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">SMS Gateway (MSG91)</h4>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">API Key</label><input type="password" className="w-full px-3 py-2 border rounded" placeholder="Enter MSG91 API key" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Sender ID</label><input className="w-full px-3 py-2 border rounded" placeholder="e.g. KITCHN" /></div>
              <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">Save SMS Config</button>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Email (SMTP)</h4>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">SMTP Host</label><input className="w-full px-3 py-2 border rounded" placeholder="smtp.gmail.com" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Port</label><input className="w-full px-3 py-2 border rounded" placeholder="587" /></div>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Username</label><input className="w-full px-3 py-2 border rounded" placeholder="your@email.com" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Password</label><input type="password" className="w-full px-3 py-2 border rounded" placeholder="App password" /></div>
              <button className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 text-sm">Save SMTP Config</button>
            </div>
          </div>
        </div>
      )}

      {/* Template Form Modal */}
      {showTemplateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Add Template</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Name *</label><input value={templateForm.name} onChange={e => setTemplateForm({...templateForm, name: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Channel</label><select value={templateForm.channel} onChange={e => setTemplateForm({...templateForm, channel: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option><option value="email">Email</option></select></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Event</label><select value={templateForm.event} onChange={e => setTemplateForm({...templateForm, event: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="order_confirmation">Order Confirmed</option><option value="order_ready">Order Ready</option><option value="feedback">Feedback</option><option value="birthday">Birthday</option><option value="promotion">Promotion</option></select></div>
              </div>
              {templateForm.channel === 'email' && <div><label className="block text-sm font-medium text-gray-700 mb-1">Subject</label><input value={templateForm.subject} onChange={e => setTemplateForm({...templateForm, subject: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>}
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Body *</label><textarea value={templateForm.body} onChange={e => setTemplateForm({...templateForm, body: e.target.value})} className="w-full px-3 py-2 border rounded" rows={4} placeholder="Use {customer_name}, {order_number}, {total} as placeholders" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={saveTemplate} disabled={sending} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">{sending ? 'Saving...' : 'Save'}</button>
              <button onClick={() => setShowTemplateForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Campaign Form Modal */}
      {showCampaignForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Send Campaign</h3>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Campaign Name</label><input value={campaignForm.name} onChange={e => setCampaignForm({...campaignForm, name: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Channel</label><select value={campaignForm.channel} onChange={e => setCampaignForm({...campaignForm, channel: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="whatsapp">WhatsApp</option><option value="sms">SMS</option></select></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Audience</label><select value={campaignForm.audience} onChange={e => setCampaignForm({...campaignForm, audience: e.target.value})} className="w-full px-3 py-2 border rounded"><option value="all">All Customers</option><option value="lapsed">Lapsed (30+ days)</option><option value="birthday">Birthday Today</option><option value="vip">VIP Customers</option></select></div>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Message *</label><textarea value={campaignForm.message} onChange={e => setCampaignForm({...campaignForm, message: e.target.value})} className="w-full px-3 py-2 border rounded" rows={4} /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={sendCampaign} disabled={sending} className="flex-1 bg-green-500 text-white py-2 rounded hover:bg-green-600 disabled:opacity-50">{sending ? 'Sending...' : 'Send Campaign'}</button>
              <button onClick={() => setShowCampaignForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
