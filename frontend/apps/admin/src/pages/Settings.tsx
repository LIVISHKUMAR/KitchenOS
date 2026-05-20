import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface TenantInfo {
  id: string
  name: string
  subscription_plan: string
  max_branches: number
}

interface BranchInfo {
  id: string
  name: string
  currency: string
}

export default function Settings() {
  const [tenant, setTenant] = useState<TenantInfo | null>(null)
  const [branches, setBranches] = useState<BranchInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [tenantRes, branchRes] = await Promise.all([
        apiClient.get('/tenants/me').catch(() => null),
        apiClient.get('/branches/').catch(() => null),
      ])
      if (tenantRes?.data) setTenant(tenantRes.data)
      if (branchRes?.data) setBranches(branchRes.data)
    } catch {
      // Silent fail
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Loading settings...</div>

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Restaurant Settings</h3>
        <p className="text-gray-500">Configure your restaurant settings, tax rates, payment methods, and more.</p>
        <div className="mt-4 space-y-4">
          <SettingRow label="Restaurant Name" value={tenant?.name || 'Not configured'} />
          <SettingRow label="Subscription Plan" value={tenant?.subscription_plan || 'basic'} />
          <SettingRow label="Branches" value={String(branches.length || tenant?.max_branches || 0)} />
          <SettingRow label="Currency" value={branches[0]?.currency || 'INR'} />
        </div>
      </div>

      {branches.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Branches</h3>
          <div className="space-y-3">
            {branches.map(branch => (
              <div key={branch.id} className="flex justify-between items-center py-2 border-b">
                <span className="font-medium">{branch.name}</span>
                <span className="text-sm text-gray-500">{branch.currency}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Integrations</h3>
        <div className="space-y-3">
          <IntegrationRow name="Payment Gateway" status="Razorpay (configured)" />
          <IntegrationRow name="WhatsApp" status="Not configured" />
          <IntegrationRow name="Email (SMTP)" status="Not configured" />
          <IntegrationRow name="Swiggy" status="Not configured" />
          <IntegrationRow name="Zomato" status="Not configured" />
        </div>
      </div>
    </div>
  )
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-2 border-b">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  )
}

function IntegrationRow({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b">
      <span className="font-medium">{name}</span>
      <span className="text-sm text-gray-500">{status}</span>
    </div>
  )
}
