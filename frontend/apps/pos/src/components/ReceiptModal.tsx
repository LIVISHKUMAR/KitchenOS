import React, { useState, useEffect } from 'react';
import { printersApi, type Printer } from '../api/printers';
import { useAuthStore } from '../stores/authStore';
import { RefundModal } from './RefundModal';

interface ReceiptModalProps {
  open: boolean;
  onClose: () => void;
  order: {
    id: string;
    order_number?: string;
    items: Array<{ name: string; quantity: number; unitPrice: number; total: number }>;
    subtotal: number;
    discount: number;
    discountLabel: string;
    tax: number;
    total: number;
    paymentMethod: string;
    tableId?: string | null;
  } | null;
}

const ReceiptModal: React.FC<ReceiptModalProps> = ({ open, onClose, order }) => {
  const [printers, setPrinters] = useState<Printer[]>([]);
  const [selectedPrinter, setSelectedPrinter] = useState<string | null>(null);
  const [printing, setPrinting] = useState(false);
  const [printed, setPrinted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refundOpen, setRefundOpen] = useState(false);
  const branchId = useAuthStore(s => s.branchId);

  useEffect(() => {
    if (open && branchId) {
      printersApi.list(branchId).then(res => {
        setPrinters(res.data);
        if (res.data.length === 1) setSelectedPrinter(res.data[0].id);
      }).catch(() => {});
    }
  }, [open, branchId]);

  if (!open || !order) return null;

  const handlePrint = async () => {
    if (!selectedPrinter) {
      setError('Select a printer');
      return;
    }
    setPrinting(true);
    setError(null);
    try {
      await printersApi.print({
        printer_id: selectedPrinter,
        job_type: 'bill',
        order_data: {
          order_number: order.order_number || order.id,
          items: order.items,
          subtotal: order.subtotal,
          tax: order.tax,
          total: order.total,
          payment_method: order.paymentMethod,
          table_id: order.tableId,
        },
      });
      setPrinted(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Print failed');
    } finally {
      setPrinting(false);
    }
  };

  const handlePrintKOT = async () => {
    if (!selectedPrinter) return;
    setPrinting(true);
    try {
      await printersApi.print({
        printer_id: selectedPrinter,
        job_type: 'kot',
        order_data: {
          order_number: order.order_number || order.id,
          items: order.items,
          table_id: order.tableId,
        },
      });
    } catch {
      // Silent fail for KOT
    } finally {
      setPrinting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-auto">
        <h2 className="text-xl font-bold mb-4">Receipt</h2>

        {/* Receipt preview */}
        <div className="bg-gray-50 p-4 rounded font-mono text-sm mb-4">
          <div className="text-center font-bold mb-2">KITCHENOS</div>
          <div className="text-center text-xs mb-3">Order #{order.order_number || order.id.slice(0, 8)}</div>
          {order.tableId && <div className="text-center text-xs mb-2">Table: {order.tableId}</div>}
          <div className="border-t border-dashed my-2" />
          {order.items.map((item, i) => (
            <div key={i} className="flex justify-between mb-1">
              <span>{item.quantity}x {item.name}</span>
              <span>₹{(item.unitPrice * item.quantity).toFixed(2)}</span>
            </div>
          ))}
          <div className="border-t border-dashed my-2" />
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>₹{order.subtotal.toFixed(2)}</span>
          </div>
          {order.discount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Discount ({order.discountLabel})</span>
              <span>-₹{order.discount.toFixed(2)}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>GST (18%)</span>
            <span>₹{order.tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold border-t mt-2 pt-2">
            <span>Total</span>
            <span>₹{order.total.toFixed(2)}</span>
          </div>
          <div className="border-t border-dashed my-2" />
          <div className="text-center text-xs">
            Paid via {order.paymentMethod.toUpperCase()}
          </div>
          <div className="text-center text-xs mt-2">Thank you!</div>
        </div>

        {/* Printer selection */}
        {printers.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Printer</label>
            <select
              value={selectedPrinter || ''}
              onChange={e => setSelectedPrinter(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Select printer...</option>
              {printers.map(p => (
                <option key={p.id} value={p.id}>{p.name} ({p.ip_address || 'local'})</option>
              ))}
            </select>
          </div>
        )}

        {printers.length === 0 && (
          <div className="mb-4 p-2 bg-yellow-50 text-yellow-700 text-sm rounded">
            No printers configured. Add a printer in Settings.
          </div>
        )}

        {error && (
          <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>
        )}

        {printed && (
          <div className="mb-4 p-2 bg-green-50 text-green-600 text-sm rounded">
            Receipt sent to printer!
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={handlePrint}
            disabled={printing || printers.length === 0}
            className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {printing ? 'Printing...' : 'Print Receipt'}
          </button>
          <button
            onClick={handlePrintKOT}
            disabled={printing || printers.length === 0}
            className="flex-1 bg-orange-500 text-white py-2 rounded-lg hover:bg-orange-600 disabled:opacity-50 font-medium"
          >
            Print KOT
          </button>
          <button
            onClick={() => setRefundOpen(true)}
            className="px-4 bg-red-100 text-red-700 py-2 rounded-lg hover:bg-red-200 font-medium text-sm"
          >
            Refund
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-lg hover:bg-gray-300 font-medium"
          >
            Close
          </button>
        </div>

        {/* Refund Modal */}
        <RefundModal
          open={refundOpen}
          onClose={() => setRefundOpen(false)}
          orderId={order.id}
          orderTotal={order.total}
        />
      </div>
    </div>
  );
};

export { ReceiptModal };
