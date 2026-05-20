import React, { useState } from 'react';
import { razorpayApi } from '../api/razorpay';

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
  const [upiStep, setUpiStep] = useState<'select' | 'qr' | 'verifying'>('select');
  const [razorpayOrder, setRazorpayOrder] = useState<{ order_id: string; key_id: string } | null>(null);
  const [upiError, setUpiError] = useState<string | null>(null);

  if (!open) return null;

  const handleUPIPayment = async () => {
    setUpiStep('qr');
    setUpiError(null);
    try {
      const res = await razorpayApi.createOrder(totalAmount);
      setRazorpayOrder({ order_id: res.data.order_id, key_id: res.data.key_id });
      // Start polling for payment confirmation
      startPaymentPolling(res.data.order_id);
    } catch (err: any) {
      setUpiError(err.response?.data?.detail || 'Failed to create UPI order');
      setUpiStep('select');
    }
  };

  const startPaymentPolling = (orderId: string) => {
    // Poll every 3 seconds for 2 minutes
    let attempts = 0;
    const maxAttempts = 40;
    const interval = setInterval(async () => {
      attempts++;
      if (attempts > maxAttempts) {
        clearInterval(interval);
        setUpiError('Payment timed out');
        setUpiStep('select');
        return;
      }
      // In production, this would check payment status via API
      // For now, just timeout
    }, 3000);
  };

  const handlePay = () => {
    if (selectedMethod === 'upi' && upiStep === 'select') {
      handleUPIPayment();
      return;
    }
    onComplete(selectedMethod);
  };

  const handleCancel = () => {
    setUpiStep('select');
    setRazorpayOrder(null);
    setUpiError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Payment</h2>
        <p className="text-2xl font-bold text-center mb-6">
          ₹{totalAmount.toFixed(2)}
        </p>

        {upiStep === 'qr' && razorpayOrder ? (
          <div className="text-center mb-6">
            <div className="bg-gray-100 p-6 rounded-lg mb-4">
              <div className="text-6xl mb-2">📱</div>
              <p className="text-sm text-gray-600 mb-2">Scan QR to pay via UPI</p>
              <div className="bg-white p-4 rounded border-2 border-dashed border-gray-300 inline-block">
                <div className="w-48 h-48 flex items-center justify-center bg-gray-50">
                  <div className="text-center">
                    <div className="text-4xl mb-2">⬛</div>
                    <p className="text-xs text-gray-500">UPI QR Code</p>
                    <p className="text-xs text-gray-400 mt-1">Order: {razorpayOrder.order_id.slice(0, 16)}...</p>
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-3">
                Amount: <span className="font-bold">₹{totalAmount.toFixed(2)}</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">Waiting for payment...</p>
            </div>
            <button
              onClick={() => { setUpiStep('select'); setRazorpayOrder(null); }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Cancel UPI payment
            </button>
          </div>
        ) : (
          <>
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

            {upiError && (
              <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{upiError}</div>
            )}
          </>
        )}

        <div className="flex gap-3">
          <button
            onClick={handlePay}
            disabled={isSubmitting}
            className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 font-medium"
          >
            {isSubmitting ? 'Processing...' : selectedMethod === 'upi' && upiStep === 'select' ? 'Pay via UPI' : 'Complete Payment'}
          </button>
          <button
            onClick={handleCancel}
            className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 font-medium"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export { PaymentModal };
