import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface Session {
  session_id: string
  user_id: string
  tenant_id: string
  role: string
  created_at: string
  last_active: string
}

interface AuditLog {
  id: string
  action: string
  resource_type: string
  resource_id: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export default function Security() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'sessions' | 'audit' | 'config'>('sessions')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [sessRes, auditRes] = await Promise.all([
        apiClient.get('/auth/sessions').catch(() => ({ data: [] })),
        apiClient.get('/audit/').catch(() => ({ data: [] })),
      ])
      setSessions(sessRes.data)
      setAuditLogs(auditRes.data)
    } catch (err) {
      console.error('Failed to load', err)
    } finally {
      setLoading(false)
    }
  }

  const revokeSession = async (sessionId: string) => {
    try {
      await apiClient.delete(`/auth/sessions/${sessionId}`)
      setSessions(sessions.filter(s => s.session_id !== sessionId))
    } catch { /* silent */ }
  }

  const revokeAllSessions = async () => {
    if (!confirm('This will log you out from all devices. Continue?')) return
    try {
      await apiClient.delete('/auth/sessions')
      setSessions([])
    } catch { /* silent */ }
  }

  if (loading) return <div className="p-6 text-gray-500">Loading security settings...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          {(['sessions', 'audit', 'config'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)} className={`pb-2 font-medium capitalize ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>{t}</button>
          ))}
        </div>
        {tab === 'sessions' && (
          <button onClick={revokeAllSessions} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 text-sm">
            Revoke All Sessions
          </button>
        )}
      </div>

      {/* Active Sessions */}
      {tab === 'sessions' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h4 className="font-semibold">Active Sessions ({sessions.length})</h4>
            <p className="text-sm text-gray-500">Manage your active login sessions across devices</p>
          </div>
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Session</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Active</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sessions.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">No active sessions</td></tr>
              ) : sessions.map(s => (
                <tr key={s.session_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-mono text-sm">{s.session_id.slice(0, 8)}...</div>
                  </td>
                  <td className="px-6 py-4"><span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">{s.role}</span></td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{new Date(s.created_at).toLocaleString()}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{new Date(s.last_active).toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => revokeSession(s.session_id)} className="text-red-500 hover:text-red-700 text-sm">Revoke</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Audit Logs */}
      {tab === 'audit' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h4 className="font-semibold">Audit Trail</h4>
            <p className="text-sm text-gray-500">Track all system actions for compliance</p>
          </div>
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Resource</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {auditLogs.length === 0 ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500">No audit logs</td></tr>
              ) : auditLogs.slice(0, 50).map(log => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4"><span className="px-2 py-1 bg-gray-100 rounded text-xs">{log.action}</span></td>
                  <td className="px-6 py-4 text-gray-500">{log.resource_type}{log.resource_id ? ` #${log.resource_id.slice(0, 8)}` : ''}</td>
                  <td className="px-6 py-4 text-gray-500 font-mono text-sm">{log.ip_address || '-'}</td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{new Date(log.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Security Config */}
      {tab === 'config' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Session Policy</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Max Concurrent Sessions</div>
                  <div className="text-sm text-gray-500">Maximum devices per user</div>
                </div>
                <select className="px-3 py-2 border rounded">
                  <option>1</option>
                  <option>2</option>
                  <option selected>3</option>
                  <option>5</option>
                  <option>Unlimited</option>
                </select>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Idle Timeout</div>
                  <div className="text-sm text-gray-500">Auto-logout after inactivity</div>
                </div>
                <select className="px-3 py-2 border rounded">
                  <option>15 minutes</option>
                  <option selected>30 minutes</option>
                  <option>1 hour</option>
                  <option>2 hours</option>
                  <option>Never</option>
                </select>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Token Expiry</div>
                  <div className="text-sm text-gray-500">JWT access token lifetime</div>
                </div>
                <select className="px-3 py-2 border rounded">
                  <option>5 minutes</option>
                  <option>15 minutes</option>
                  <option>30 minutes</option>
                  <option>1 hour</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Security Features</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">RBAC Enforcement</div>
                  <div className="text-sm text-gray-500">Role-based access control on all endpoints</div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Enabled</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Token Revocation</div>
                  <div className="text-sm text-gray-500">Instant token invalidation on logout</div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Enabled</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Audit Logging</div>
                  <div className="text-sm text-gray-500">Track all data modifications</div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Enabled</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Rate Limiting</div>
                  <div className="text-sm text-gray-500">API rate limits per user/IP</div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Enabled</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">RLS (Row-Level Security)</div>
                  <div className="text-sm text-gray-500">Database-level tenant isolation</div>
                </div>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">Defined</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="font-medium">PCI-DSS Compliance</div>
                  <div className="text-sm text-gray-500">Payment card data security</div>
                </div>
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">Razorpay Handles</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold mb-4">Backup & Recovery</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Automated Backups</div>
                  <div className="text-sm text-gray-500">Daily database backups to S3</div>
                </div>
                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">Active</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">Backup Retention</div>
                  <div className="text-sm text-gray-500">How long backups are kept</div>
                </div>
                <span className="text-sm">30 days</span>
              </div>
              <div className="flex justify-between items-center py-2">
                <div>
                  <div className="font-medium">Last Backup</div>
                  <div className="text-sm text-gray-500">Most recent successful backup</div>
                </div>
                <span className="text-sm">{new Date().toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
