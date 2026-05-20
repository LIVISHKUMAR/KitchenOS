import React, { useState, useRef, useEffect } from 'react';
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
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus trap and escape key
  useEffect(() => {
    if (!open) return;

    // Focus the close button on open
    closeButtonRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }

      // Focus trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  const handleUPIPayment = async () => {
    setUpiStep('qr');
    setUpiError(null);
    try {
      const res = await razorpayApi.createOrder(totalAmount);
      setRazorpayOrder({ order_id: res.data.order_id, key_id: res.data.key_id });
    } catch (err: any) {
      setUpiError(err.response?.data?.detail || 'Failed to create UPI order');
      setUpiStep('select');
    }
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
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="payment-title"
      ref={modalRef}
    >
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
        <h2 id="payment-title" className="text-xl font-bold mb-4 text-center">Payment</h2>
        <p className="text-3xl font-bold text-center mb-6 text-gray-900" aria-live="polite">
          ₹{totalAmount.toFixed(2)}
        </p>

        {upiStep === 'qr' && razorpayOrder ? (
          <div className="text-center mb-6">
            <div className="bg-gray-50 p-6 rounded-xl mb-4">
              <div className="text-5xl mb-3" aria-hidden="true">📱</div>
              <p className="text-sm text-gray-600 mb-2">Scan QR to pay via UPI</p>
              <div className="bg-white p-4 rounded-lg border-2 border-dashed border-gray-200 inline-block">
                <div className="w-48 h-48 flex items-center justify-center bg-gray-50 rounded">
                  <div className="text-center">
                    <div className="text-4xl mb-2" aria-hidden="true">⬛</div>
                    <p className="text-xs text-gray-500">UPI QR Code</p>
                    <p className="text-xs text-gray-400 mt-1">Order: {razorpayOrder.order_id.slice(0, 16)}...</p>
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-3">
                Amount: <span className="font-bold">₹{totalAmount.toFixed(2)}</span>
              </p>
              <p className="text-xs text-gray-400 mt-1 animate-pulse">Waiting for payment...</p>
            </div>
            <button
              onClick={() => { setUpiStep('select'); setRazorpayOrder(null); }}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Cancel UPI payment
            </button>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 mb-6" role="radiogroup" aria-label="Payment method">
              {PAYMENT_METHODS.map(method => (
                <button
                  key={method.id}
                  onClick={() => setSelectedMethod(method.id)}
                  role="radio"
                  aria-checked={selectedMethod === method.id}
                  className={`p-4 border rounded-xl text-center transition-all ${
                    selectedMethod === method.id
                      ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-sm'
                      : 'border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                  }`}
                >
                  <span className="text-2xl block mb-1" aria-hidden="true">{method.icon}</span>
                  <div className="text-sm font-medium">{method.label}</div>
                </button>
              ))}
            </div>

            {upiError && (
              <div className="mb-4 p-3 bg-red-50 text-red-600 text-sm rounded-lg" role="alert">
                {upiError}
              </div>
            )}
          </>
        )}

        <div className="flex gap-3">
          <button
            onClick={handlePay}
            disabled={isSubmitting}
            className="flex-1 bg-green-600 text-white py-3 rounded-xl hover:bg-green-700 disabled:opacity-50 font-medium transition-colors"
          >
            {isSubmitting ? 'Processing...' : selectedMethod === 'upi' && upiStep === 'select' ? 'Pay via UPI' : 'Complete Payment'}
          </button>
          <button
            ref={closeButtonRef}
            onClick={handleCancel}
            className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-xl hover:bg-gray-200 font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export { PaymentModal };
