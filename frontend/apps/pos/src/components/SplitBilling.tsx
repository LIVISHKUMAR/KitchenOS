import React, { useState } from 'react';

interface SplitItem {
  name: string;
  quantity: number;
  unitPrice: number;
  total: number;
  assignedTo: number | null; // split index or null
}

interface SplitBillingProps {
  open: boolean;
  onClose: () => void;
  items: Array<{ name: string; quantity: number; unitPrice: number; total: number }>;
  totalAmount: number;
  onConfirm: (splits: Array<{ items: typeof items; amount: number }>) => void;
}

type SplitMode = 'equal' | 'by-item' | 'custom';

export const SplitBilling: React.FC<SplitBillingProps> = ({ open, onClose, items, totalAmount, onConfirm }) => {
  const [mode, setMode] = useState<SplitMode>('equal');
  const [splitCount, setSplitCount] = useState(2);
  const [assignments, setAssignments] = useState<number[]>(items.map(() => 0));
  const [customAmounts, setCustomAmounts] = useState<number[]>([0, 0]);

  if (!open) return null;

  const handleEqualSplit = () => {
    const perPerson = totalAmount / splitCount;
    const splits = Array.from({ length: splitCount }, (_, i) => ({
      items: i === 0 ? items : [],
      amount: perPerson,
    }));
    onConfirm(splits);
    onClose();
  };

  const handleByItemSplit = () => {
    const splits: Array<{ items: typeof items; amount: number }> = Array.from({ length: splitCount }, () => ({
      items: [],
      amount: 0,
    }));
    items.forEach((item, i) => {
      const splitIdx = assignments[i] ?? 0;
      splits[splitIdx].items.push(item);
      splits[splitIdx].amount += item.total;
    });
    onConfirm(splits);
    onClose();
  };

  const handleCustomSplit = () => {
    const splits = customAmounts.map((amount, i) => ({
      items: i === 0 ? items : [],
      amount,
    }));
    onConfirm(splits);
    onClose();
  };

  const handleConfirm = () => {
    if (mode === 'equal') handleEqualSplit();
    else if (mode === 'by-item') handleByItemSplit();
    else handleCustomSplit();
  };

  const equalAmount = totalAmount / splitCount;
  const customTotal = customAmounts.reduce((s, a) => s + a, 0);
  const customDiff = totalAmount - customTotal;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-auto">
        <h2 className="text-xl font-bold mb-4">Split Bill</h2>

        {/* Mode Selector */}
        <div className="flex gap-2 mb-4">
          {(['equal', 'by-item', 'custom'] as SplitMode[]).map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-2 rounded text-sm font-medium ${
                mode === m ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {m === 'equal' ? 'Equal' : m === 'by-item' ? 'By Item' : 'Custom'}
            </button>
          ))}
        </div>

        {/* Equal Split */}
        {mode === 'equal' && (
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Number of splits</label>
              <div className="flex gap-2">
                {[2, 3, 4, 5, 6].map(n => (
                  <button
                    key={n}
                    onClick={() => setSplitCount(n)}
                    className={`w-10 h-10 rounded ${splitCount === n ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded text-center">
              <div className="text-sm text-gray-500">Each person pays</div>
              <div className="text-3xl font-bold text-green-600">₹{equalAmount.toFixed(2)}</div>
            </div>
          </div>
        )}

        {/* By Item Split */}
        {mode === 'by-item' && (
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Number of splits</label>
              <div className="flex gap-2">
                {[2, 3, 4].map(n => (
                  <button
                    key={n}
                    onClick={() => setSplitCount(n)}
                    className={`w-10 h-10 rounded ${splitCount === n ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2 mb-4">
              {items.map((item, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <span className="text-sm">{item.quantity}x {item.name}</span>
                  <div className="flex gap-1">
                    {Array.from({ length: splitCount }, (_, s) => (
                      <button
                        key={s}
                        onClick={() => {
                          const newAssignments = [...assignments];
                          newAssignments[i] = s;
                          setAssignments(newAssignments);
                        }}
                        className={`w-8 h-8 rounded text-xs ${
                          assignments[i] === s ? 'bg-blue-500 text-white' : 'bg-gray-200'
                        }`}
                      >
                        {s + 1}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2">
              {Array.from({ length: splitCount }, (_, s) => {
                const splitTotal = items.reduce((sum, item, i) =>
                  assignments[i] === s ? sum + item.total : sum, 0);
                return (
                  <div key={s} className="bg-gray-50 p-3 rounded text-center">
                    <div className="text-xs text-gray-500">Person {s + 1}</div>
                    <div className="font-bold">₹{splitTotal.toFixed(0)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Custom Split */}
        {mode === 'custom' && (
          <div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Number of splits</label>
              <div className="flex gap-2">
                {[2, 3, 4].map(n => (
                  <button
                    key={n}
                    onClick={() => {
                      setSplitCount(n);
                      setCustomAmounts(Array(n).fill(0));
                    }}
                    className={`w-10 h-10 rounded ${splitCount === n ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2 mb-4">
              {Array.from({ length: splitCount }, (_, s) => (
                <div key={s} className="flex items-center gap-3">
                  <span className="text-sm w-20">Person {s + 1}:</span>
                  <input
                    type="number"
                    value={customAmounts[s] || ''}
                    onChange={e => {
                      const newAmounts = [...customAmounts];
                      newAmounts[s] = parseFloat(e.target.value) || 0;
                      setCustomAmounts(newAmounts);
                    }}
                    className="flex-1 px-3 py-2 border rounded"
                    placeholder="₹0"
                  />
                </div>
              ))}
            </div>
            <div className={`p-3 rounded text-center ${Math.abs(customDiff) < 0.01 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
              {Math.abs(customDiff) < 0.01 ? 'Amounts match!' : `Remaining: ₹${customDiff.toFixed(2)}`}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 mt-6">
          <button
            onClick={handleConfirm}
            disabled={mode === 'custom' && Math.abs(customDiff) > 0.01}
            className="flex-1 bg-green-500 text-white py-2 rounded hover:bg-green-600 disabled:opacity-50 font-medium"
          >
            Confirm Split
          </button>
          <button onClick={onClose} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
