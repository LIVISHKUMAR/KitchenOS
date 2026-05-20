import React, { useState } from 'react';
import apiClient from '../api/client';
import { useAuthStore } from '../stores/authStore';

interface ZReport {
  date: string;
  summary: {
    total_orders: number;
    total_revenue: number;
    total_tax: number;
    total_discount: number;
    avg_order_value: number;
  };
  payment_breakdown: Array<{ method: string; count: number; total: number }>;
  order_types: Array<{ type: string; count: number; revenue: number }>;
  cash_reconciliation: {
    cash_expected: number;
    cash_counted: number | null;
    discrepancy: number | null;
  };
}

interface ShiftClosingProps {
  open: boolean;
  onClose: () => void;
}

export const ShiftClosing: React.FC<ShiftClosingProps> = ({ open, onClose }) => {
  const branchId = useAuthStore(s => s.branchId);
  const [step, setStep] = useState<'count' | 'report'>('count');
  const [cashCounted, setCashCounted] = useState('');
  const [report, setReport] = useState<ZReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post('/shifts/z-report', {
        branch_id: branchId,
        cash_counted: cashCounted ? parseFloat(cashCounted) : null,
      });
      setReport(res.data);
      setStep('report');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStep('count');
    setCashCounted('');
    setReport(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-auto">
        <h2 className="text-xl font-bold mb-4">Shift Closing - Z Report</h2>

        {step === 'count' && (
          <div>
            <p className="text-gray-600 text-sm mb-4">
              Count your cash drawer and enter the total amount below.
            </p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Cash Counted (₹)</label>
              <input
                type="number"
                value={cashCounted}
                onChange={e => setCashCounted(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg text-lg"
                placeholder="Enter cash amount"
                autoFocus
              />
            </div>
            {error && <div className="mb-4 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}
            <div className="flex gap-2">
              <button
                onClick={handleGenerateReport}
                disabled={loading}
                className="flex-1 bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium"
              >
                {loading ? 'Generating...' : 'Generate Z Report'}
              </button>
              <button
                onClick={handleClose}
                className="flex-1 bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {step === 'report' && report && (
          <div>
            <div className="text-center mb-4">
              <div className="text-sm text-gray-500">{report.date}</div>
              <div className="text-2xl font-bold">Z Report</div>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-xs text-gray-500">Total Orders</div>
                  <div className="text-xl font-bold">{report.summary.total_orders}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Total Revenue</div>
                  <div className="text-xl font-bold text-green-600">₹{report.summary.total_revenue.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Tax Collected</div>
                  <div className="font-bold">₹{report.summary.total_tax.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Discounts Given</div>
                  <div className="font-bold">₹{report.summary.total_discount.toFixed(2)}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-gray-500">Average Order Value</div>
                  <div className="font-bold">₹{report.summary.avg_order_value.toFixed(2)}</div>
                </div>
              </div>
            </div>

            {/* Payment Breakdown */}
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-2">Payment Methods</h4>
              <div className="space-y-1">
                {report.payment_breakdown.map((p, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="capitalize">{p.method}</span>
                    <span>₹{p.total.toFixed(2)} ({p.count})</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Cash Reconciliation */}
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <h4 className="text-sm font-semibold mb-2">Cash Reconciliation</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Expected:</span>
                  <span className="font-bold">₹{report.cash_reconciliation.cash_expected.toFixed(2)}</span>
                </div>
                {report.cash_reconciliation.cash_counted !== null && (
                  <>
                    <div className="flex justify-between">
                      <span>Counted:</span>
                      <span className="font-bold">₹{report.cash_reconciliation.cash_counted.toFixed(2)}</span>
                    </div>
                    <div className={`flex justify-between font-bold ${
                      (report.cash_reconciliation.discrepancy || 0) === 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      <span>Discrepancy:</span>
                      <span>₹{(report.cash_reconciliation.discrepancy || 0).toFixed(2)}</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            <button
              onClick={handleClose}
              className="w-full bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 font-medium"
            >
              Close Shift
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
