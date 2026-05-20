import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface Reservation {
  id: string
  customer_name: string
  customer_phone: string | null
  party_size: number
  reservation_time: string
  table_id: string | null
  status: string
  notes: string | null
}

interface WaitlistEntry {
  id: string
  customer_name: string
  customer_phone: string
  party_size: number
  status: string
  estimated_wait_minutes: number
  notes: string | null
  created_at: string
}

export default function Reservations() {
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'reservations' | 'waitlist'>('reservations')
  const [showForm, setShowForm] = useState(false)
  const [showWaitlistForm, setShowWaitlistForm] = useState(false)
  const [form, setForm] = useState({ customer_name: '', customer_phone: '', party_size: '2', reservation_time: '', table_id: '', notes: '' })
  const [waitlistForm, setWaitlistForm] = useState({ customer_name: '', customer_phone: '', party_size: '2', notes: '' })
  const [saving, setSaving] = useState(false)
  const [filterDate, setFilterDate] = useState(new Date().toISOString().slice(0, 10))

  useEffect(() => { loadData() }, [filterDate])

  const loadData = async () => {
    try {
      const [resRes, waitRes] = await Promise.all([
        apiClient.get('/reservations/', { params: { branch_id: '', date: filterDate } }).catch(() => ({ data: [] })),
        apiClient.get('/reservations/waitlist').catch(() => ({ data: [] })),
      ])
      setReservations(Array.isArray(resRes.data) ? resRes.data : [])
      setWaitlist(Array.isArray(waitRes.data) ? waitRes.data : [])
    } catch (err) {
      console.error('Failed to load', err)
    } finally {
      setLoading(false)
    }
  }

  const createReservation = async () => {
    if (!form.customer_name || !form.reservation_time) return
    setSaving(true)
    try {
      await apiClient.post('/reservations/', {
        branch_id: '',
        customer_name: form.customer_name,
        customer_phone: form.customer_phone || null,
        party_size: parseInt(form.party_size) || 2,
        reservation_time: form.reservation_time,
        table_id: form.table_id || null,
        notes: form.notes || null,
      })
      setShowForm(false)
      setForm({ customer_name: '', customer_phone: '', party_size: '2', reservation_time: '', table_id: '', notes: '' })
      loadData()
    } catch (err: any) {
      console.error('Failed to create reservation', err)
    } finally {
      setSaving(false)
    }
  }

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await apiClient.put(`/reservations/${id}/status`, null, { params: { new_status: newStatus } })
      loadData()
    } catch { /* silent */ }
  }

  const addToWaitlist = async () => {
    if (!waitlistForm.customer_name) return
    setSaving(true)
    try {
      await apiClient.post('/reservations/waitlist', {
        customer_name: waitlistForm.customer_name,
        customer_phone: waitlistForm.customer_phone,
        party_size: parseInt(waitlistForm.party_size) || 2,
        notes: waitlistForm.notes || null,
      })
      setShowWaitlistForm(false)
      setWaitlistForm({ customer_name: '', customer_phone: '', party_size: '2', notes: '' })
      loadData()
    } catch { /* silent */ } finally { setSaving(false) }
  }

  const seatWaitlist = async (id: string) => {
    try { await apiClient.put(`/reservations/waitlist/${id}/seat`); loadData() } catch { /* silent */ }
  }

  const removeWaitlist = async (id: string) => {
    try { await apiClient.delete(`/reservations/waitlist/${id}`); loadData() } catch { /* silent */ }
  }

  const getTimeSince = (dateStr: string) => {
    const mins = Math.floor((Date.now() - new Date(dateStr).getTime()) / 60000)
    return mins < 1 ? 'Just now' : mins < 60 ? `${mins}m ago` : `${Math.floor(mins / 60)}h ${mins % 60}m ago`
  }

  const statusColors: Record<string, string> = {
    confirmed: 'bg-blue-100 text-blue-700',
    seated: 'bg-green-100 text-green-700',
    cancelled: 'bg-gray-100 text-gray-500',
    no_show: 'bg-red-100 text-red-700',
  }

  if (loading) return <div className="p-6 text-gray-500">Loading...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          <button onClick={() => setTab('reservations')} className={`pb-2 font-medium ${tab === 'reservations' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>
            Reservations ({reservations.length})
          </button>
          <button onClick={() => setTab('waitlist')} className={`pb-2 font-medium ${tab === 'waitlist' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'}`}>
            Waitlist ({waitlist.length})
          </button>
        </div>
        <div className="flex gap-2">
          {tab === 'reservations' && (
            <>
              <input type="date" value={filterDate} onChange={e => setFilterDate(e.target.value)} className="px-3 py-2 border rounded text-sm" />
              <button onClick={() => setShowForm(true)} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">+ New Reservation</button>
            </>
          )}
          {tab === 'waitlist' && (
            <button onClick={() => setShowWaitlistForm(true)} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm">+ Add to Waitlist</button>
          )}
        </div>
      </div>

      {/* Reservations */}
      {tab === 'reservations' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Party</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {reservations.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">No reservations for this date</td></tr>
              ) : reservations.map(r => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">{r.customer_name}</td>
                  <td className="px-6 py-4 text-gray-500">{r.customer_phone || '-'}</td>
                  <td className="px-6 py-4">{r.party_size} people</td>
                  <td className="px-6 py-4">{new Date(r.reservation_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                  <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-xs ${statusColors[r.status] || ''}`}>{r.status}</span></td>
                  <td className="px-6 py-4 text-right">
                    {r.status === 'confirmed' && (
                      <>
                        <button onClick={() => updateStatus(r.id, 'seated')} className="text-green-500 hover:text-green-700 text-sm mr-3">Seat</button>
                        <button onClick={() => updateStatus(r.id, 'cancelled')} className="text-red-500 hover:text-red-700 text-sm mr-3">Cancel</button>
                        <button onClick={() => updateStatus(r.id, 'no_show')} className="text-gray-500 hover:text-gray-700 text-sm">No Show</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Waitlist */}
      {tab === 'waitlist' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Party</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Waiting</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Est. Wait</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {waitlist.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500">Waitlist is empty</td></tr>
              ) : waitlist.map((w, i) => (
                <tr key={w.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium">
                    <span className="text-gray-400 mr-2">#{i + 1}</span>
                    {w.customer_name}
                  </td>
                  <td className="px-6 py-4 text-gray-500">{w.customer_phone}</td>
                  <td className="px-6 py-4">{w.party_size} people</td>
                  <td className="px-6 py-4 text-gray-500">{getTimeSince(w.created_at)}</td>
                  <td className="px-6 py-4">{w.estimated_wait_minutes} min</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => seatWaitlist(w.id)} className="text-green-500 hover:text-green-700 text-sm mr-3">Seat</button>
                    <button onClick={() => removeWaitlist(w.id)} className="text-red-500 hover:text-red-700 text-sm">Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Reservation Form */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">New Reservation</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Customer Name *</label><input value={form.customer_name} onChange={e => setForm({...form, customer_name: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Phone</label><input value={form.customer_phone} onChange={e => setForm({...form, customer_phone: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Party Size</label><input type="number" value={form.party_size} onChange={e => setForm({...form, party_size: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Date & Time *</label><input type="datetime-local" value={form.reservation_time} onChange={e => setForm({...form, reservation_time: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              </div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} className="w-full px-3 py-2 border rounded" placeholder="Special requests" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={createReservation} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">{saving ? 'Saving...' : 'Create'}</button>
              <button onClick={() => setShowForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Waitlist Form */}
      {showWaitlistForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Add to Waitlist</h3>
            <div className="space-y-3">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Name *</label><input value={waitlistForm.customer_name} onChange={e => setWaitlistForm({...waitlistForm, customer_name: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Phone</label><input value={waitlistForm.customer_phone} onChange={e => setWaitlistForm({...waitlistForm, customer_phone: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Party Size</label><input type="number" value={waitlistForm.party_size} onChange={e => setWaitlistForm({...waitlistForm, party_size: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Notes</label><input value={waitlistForm.notes} onChange={e => setWaitlistForm({...waitlistForm, notes: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={addToWaitlist} disabled={saving} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50">{saving ? 'Adding...' : 'Add'}</button>
              <button onClick={() => setShowWaitlistForm(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
