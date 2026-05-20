import React, { useState } from 'react';
import { paymentsApi } from '../api/payments';

interface RefundModalProps {
  open: boolean;
  onClose: () => void;
  orderId: string;
  orderTotal: number;
  onRefundComplete?: () => void;
}

export const RefundModal: React.FC<RefundModalProps> = ({ open, onClose, orderId, orderTotal, onRefundComplete }) => {
  const [mode, setMode] = useState<'full' | 'partial'>('full');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!open) return null;

  const handleRefund = async () => {
    const refundAmount = mode === 'full' ? orderTotal : parseFloat(amount);
    if (!refundAmount || refundAmount <= 0) {
      setError('Enter a valid amount');
      return;
    }
    if (refundAmount > orderTotal) {
      setError('Refund cannot exceed order total');
      return;
    }
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Get payment for this order
      const paymentsRes = await paymentsApi.getByOrder(orderId);
      const payment = paymentsRes.data[0];
      if (!payment) {
        setError('No payment found for this order');
        setLoading(false);
        return;
      }

      await paymentsApi.refund({
        payment_id: payment.id,
        amount: refundAmount,
        reason: reason.trim(),
      });
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setReason('');
        setAmount('');
        onRefundComplete?.();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Refund failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVoid = async () => {
    if (!reason.trim()) {
      setError('Reason is required for void');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const paymentsRes = await paymentsApi.getByOrder(orderId);
      const payment = paymentsRes.data[0];
      if (!payment) {
        setError('No payment found');
        setLoading(false);
        return;
      }
      await paymentsApi.void(payment.id, reason.trim());
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setReason('');
        onRefundComplete?.();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Void failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Refund / Void</h2>

        {success ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">✅</div>
            <div className="text-lg font-bold text-green-600">Refund Processed</div>
          </div>
        ) : (
          <>
            {/* Mode Selector */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setMode('full')}
                className={`flex-1 py-2 rounded text-sm font-medium ${mode === 'full' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
              >
                Full Refund
              </button>
              <button
                onClick={() => setMode('partial')}
                className={`flex-1 py-2 rounded text-sm font-medium ${mode === 'partial' ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
              >
                Partial Refund
              </button>
            </div>

            <div className="mb-4 text-sm text-gray-600">
              Order Total: <span className="font-bold">₹{orderTotal.toFixed(2)}</span>
            </div>

            {mode === 'partial' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Refund Amount</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  max={orderTotal}
                  placeholder="₹0.00"
                />
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Reason *</label>
              <select
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="w-full px-3 py-2 border rounded mb-2"
              >
                <option value="">Select reason...</option>
                <option value="wrong_order">Wrong order</option>
                <option value="customer_request">Customer request</option>
                <option value="quality_issue">Quality issue</option>
                <option value="duplicate_charge">Duplicate charge</option>
                <option value="other">Other</option>
              </select>
              {reason === 'other' && (
                <input
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  className="w-full px-3 py-2 border rounded"
                  placeholder="Specify reason"
                />
              )}
            </div>

            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

            <div className="flex gap-2">
              <button
                onClick={handleRefund}
                disabled={loading}
                className="flex-1 bg-orange-500 text-white py-2 rounded hover:bg-orange-600 disabled:opacity-50 font-medium"
              >
                {loading ? 'Processing...' : `Refund ₹${mode === 'full' ? orderTotal.toFixed(2) : (parseFloat(amount) || 0).toFixed(2)}`}
              </button>
              <button
                onClick={handleVoid}
                disabled={loading}
                className="px-4 bg-red-500 text-white py-2 rounded hover:bg-red-600 disabled:opacity-50"
                title="Void entire payment"
              >
                Void
              </button>
              <button onClick={onClose} className="px-4 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">
                Cancel
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
