import React, { memo } from 'react';
import { CustomerLookup } from '../CustomerLookup';
import { TableSelection } from '../TableSelection';
import type { Customer } from '../../api/customers';
import type { HeldOrder } from '../../stores/orderStore';

interface POSSidebarProps {
  selectedCustomer: Customer | null;
  onSelectCustomer: (customer: Customer | null) => void;
  selectedTableId: string | null;
  onSelectTable: (tableId: string | null) => void;
  itemCount: number;
  subtotal: number;
  discountAmount: number;
  discountLabel: string;
  discount: number;
  tax: number;
  total: number;
  error: string | null;
  isSubmitting: boolean;
  couponCode: string;
  setCouponCode: (code: string) => void;
  couponLoading: boolean;
  couponError: string | null;
  onApplyCoupon: () => void;
  onRemoveDiscount: () => void;
  onManualDiscount: () => void;
  onCheckout: () => void;
  onHold: () => void;
  onSplit: () => void;
  onClear: () => void;
  heldOrders: HeldOrder[];
  onResumeOrder: (id: string) => void;
  onRemoveHeldOrder: (id: string) => void;
}

const POSSidebar: React.FC<POSSidebarProps> = memo(({
  selectedCustomer, onSelectCustomer,
  selectedTableId, onSelectTable,
  itemCount, subtotal, discountAmount, discountLabel, discount, tax, total,
  error, isSubmitting,
  couponCode, setCouponCode, couponLoading, couponError,
  onApplyCoupon, onRemoveDiscount, onManualDiscount,
  onCheckout, onHold, onSplit, onClear,
  heldOrders, onResumeOrder, onRemoveHeldOrder,
}) => {
  return (
    <aside className="w-64 bg-white border-r flex flex-col">
      <div className="p-4 border-b">
        <h1 className="text-lg font-bold text-gray-800">KitchenOS</h1>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="border-b">
          <div className="px-4 pt-3 pb-1">
            <h3 className="font-semibold text-sm">Customer</h3>
          </div>
          <CustomerLookup selectedCustomer={selectedCustomer} onSelect={onSelectCustomer} />
        </div>
        <TableSelection selectedTable={selectedTableId} onTableSelect={onSelectTable} />
      </div>

      {/* Coupon Input */}
      {itemCount > 0 && !discountAmount && (
        <div className="p-3 border-b">
          <div className="flex gap-1">
            <input
              type="text"
              placeholder="Coupon code"
              value={couponCode}
              onChange={e => setCouponCode(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && onApplyCoupon()}
              className="flex-1 px-2 py-1 border rounded text-sm"
            />
            <button onClick={onApplyCoupon} disabled={couponLoading || !couponCode.trim()} className="px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50">
              {couponLoading ? '...' : 'Apply'}
            </button>
            <button onClick={onManualDiscount} className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300" title="Manual discount">₹</button>
          </div>
          {couponError && <div className="text-xs text-red-500 mt-1">{couponError}</div>}
        </div>
      )}

      {/* Order Summary */}
      <div className="p-4 border-t">
        <div className="space-y-1 text-sm mb-3">
          <div className="flex justify-between">
            <span className="text-gray-600">Items:</span>
            <span className="font-medium">{itemCount}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Subtotal:</span>
            <span className="font-medium">₹{subtotal.toFixed(2)}</span>
          </div>
          {discountAmount > 0 && (
            <div className="flex justify-between text-green-600">
              <span className="flex items-center gap-1">
                Discount ({discountLabel})
                <button onClick={onRemoveDiscount} className="text-xs text-red-400 hover:text-red-600">x</button>
              </span>
              <span className="font-medium">-₹{discount.toFixed(2)}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-600">Tax (18%):</span>
            <span className="font-medium">₹{tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between pt-2 border-t">
            <span className="font-bold">Total:</span>
            <span className="font-bold text-lg">₹{total.toFixed(2)}</span>
          </div>
        </div>

        {error && <div className="mb-2 p-2 bg-red-50 text-red-600 text-sm rounded">{error}</div>}

        <button onClick={onCheckout} disabled={itemCount === 0 || isSubmitting} className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium">
          {isSubmitting ? 'Processing...' : `Checkout ₹${total.toFixed(2)}`}
        </button>

        <div className="flex gap-2 mt-2">
          <button onClick={onHold} disabled={itemCount === 0} className="flex-1 bg-yellow-500 text-white py-2 rounded hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium">Hold (F3)</button>
          <button onClick={onSplit} disabled={itemCount === 0} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium">Split</button>
          <button onClick={onClear} disabled={itemCount === 0} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm">Clear</button>
        </div>
      </div>

      {/* Held Orders */}
      {heldOrders.length > 0 && (
        <div className="border-t p-3">
          <h3 className="font-semibold text-sm mb-2 text-gray-600">Held Orders ({heldOrders.length})</h3>
          <div className="space-y-1 max-h-40 overflow-auto">
            {heldOrders.map(held => (
              <div key={held.id} className="flex items-center justify-between p-2 bg-yellow-50 rounded border border-yellow-200 text-sm">
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{held.customerName || `Order ${held.id.slice(-4)}`}</div>
                  <div className="text-xs text-gray-500">
                    {held.items.length} items · ₹{held.items.reduce((s, i) => s + i.unitPrice * i.quantity, 0).toFixed(0)}
                    {held.tableId && ` · T${held.tableId}`}
                  </div>
                </div>
                <div className="flex gap-1 ml-2">
                  <button onClick={() => onResumeOrder(held.id)} className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600">Resume</button>
                  <button onClick={() => onRemoveHeldOrder(held.id)} className="px-1 py-1 text-red-400 hover:text-red-600 text-xs">✕</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
});

POSSidebar.displayName = 'POSSidebar';
export { POSSidebar };
