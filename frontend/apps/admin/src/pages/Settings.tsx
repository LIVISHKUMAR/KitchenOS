import React from 'react'

export default function Settings() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Restaurant Settings</h3>
        <p className="text-gray-500">Configure your restaurant settings, tax rates, payment methods, and more.</p>
        <div className="mt-4 space-y-4">
          <SettingRow label="Restaurant Name" value="Demo Restaurant" />
          <SettingRow label="Subscription Plan" value="Professional" />
          <SettingRow label="Branches" value="1" />
          <SettingRow label="Currency" value="INR (₹)" />
          <SettingRow label="Tax Rate" value="5% GST" />
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Integrations</h3>
        <div className="space-y-3">
          <IntegrationRow name="Payment Gateway" status="Not configured" />
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
