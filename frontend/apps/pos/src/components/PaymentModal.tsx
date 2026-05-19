import React, { useState } from 'react';

interface PaymentModalProps {
  open: boolean;
  onClose: () => void;
  onComplete: (paymentMethod: string) => void;
  totalAmount: number;
  isSubmitting?: boolean;
}

const PAYMENT_METHODS = [
  { id: 'cash', label: 'Cash', icon: '💵' },
  { id: 'card', label: 'Card', icon: '💳' },
  { id: 'upi', label: 'UPI', icon: '📱' },
  { id: 'wallet', label: 'Wallet', icon: '👛' },
];

const PaymentModal: React.FC<PaymentModalProps> = ({ open, onClose, onComplete, totalAmount, isSubmitting }) => {
  const [selectedMethod, setSelectedMethod] = useState('cash');

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Payment</h2>
        <p className="text-2xl font-bold text-center mb-6">
          ₹{totalAmount.toFixed(2)}
        </p>

        {/* Payment methods */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {PAYMENT_METHODS.map(method => (
            <button
              key={method.id}
              onClick={() => setSelectedMethod(method.id)}
              className={`p-3 border rounded-lg text-center transition-colors ${
                selectedMethod === method.id
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <span className="text-2xl">{method.icon}</span>
              <div className="text-sm font-medium mt-1">{method.label}</div>
            </button>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => onComplete(selectedMethod)}
            disabled={isSubmitting}
            className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? 'Processing...' : 'Complete Payment'}
          </button>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-medium"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export { PaymentModal };
