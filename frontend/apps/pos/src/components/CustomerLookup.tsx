import React, { useState } from 'react';
import { customersApi, type Customer } from '../api/customers';

interface CustomerLookupProps {
  onSelect: (customer: Customer | null) => void;
  selectedCustomer: Customer | null;
}

const CustomerLookup: React.FC<CustomerLookupProps> = ({ onSelect, selectedCustomer }) => {
  const [phone, setPhone] = useState('');
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!phone || phone.length < 3) return;
    setSearching(true);
    setError(null);
    try {
      const res = await customersApi.getByPhone(phone);
      if (res.data) {
        onSelect(res.data);
      } else {
        setError('Customer not found');
      }
    } catch {
      setError('Customer not found');
    } finally {
      setSearching(false);
    }
  };

  const handleClear = () => {
    setPhone('');
    onSelect(null);
    setError(null);
  };

  if (selectedCustomer) {
    return (
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center justify-between mb-1">
          <span className="font-medium text-sm text-blue-800">{selectedCustomer.name}</span>
          <button onClick={handleClear} className="text-xs text-blue-500 hover:text-blue-700">
            Clear
          </button>
        </div>
        <div className="text-xs text-blue-600">{selectedCustomer.phone}</div>
        <div className="flex gap-3 mt-1 text-xs text-blue-600">
          <span>{selectedCustomer.loyalty_points} pts</span>
          <span>{selectedCustomer.total_orders} orders</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3">
      <div className="flex gap-2">
        <input
          type="tel"
          placeholder="Phone number"
          value={phone}
          onChange={e => setPhone(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          className="flex-1 px-3 py-1.5 border rounded text-sm"
          maxLength={15}
        />
        <button
          onClick={handleSearch}
          disabled={searching || phone.length < 3}
          className="px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
        >
          {searching ? '...' : 'Find'}
        </button>
      </div>
      {error && <div className="text-xs text-red-500 mt-1">{error}</div>}
    </div>
  );
};

export { CustomerLookup };
