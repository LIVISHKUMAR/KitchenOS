import React, { useState, useCallback, useMemo } from 'react';
import { useOrderStore } from '../stores/orderStore';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../components/Toast';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { MenuGrid } from '../components/MenuGrid';
import { Cart } from '../components/Cart';
import { NumPad } from '../components/NumPad';
import { PaymentModal } from '../components/PaymentModal';
import { ReceiptModal } from '../components/ReceiptModal';
import { SplitBilling } from '../components/SplitBilling';
import { ShiftClosing } from '../components/ShiftClosing';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { TableSelection } from '../components/TableSelection';
import { CustomerLookup } from '../components/CustomerLookup';
import type { MenuItem } from '../api';
import type { Customer } from '../api/customers';
import { couponsApi } from '../api/coupons';

interface ReceiptData {
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
}

const POSPage = () => {
  const { logout } = useAuthStore();
  const { showToast } = useToast();
  const {
    currentOrder,
    selectedTableId,
    isSubmitting,
    error,
    discountAmount,
    discountLabel,
    heldOrders,
    addItem,
    updateItemQuantity,
    removeItem,
    clearCart,
    setSelectedTable,
    setDiscount,
    completePayment,
    holdCurrentOrder,
    resumeOrder,
    removeHeldOrder,
    getSubtotal,
    getDiscount,
    getTax,
    getTotal,
    getItemCount,
  } = useOrderStore();

  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [splitBillingOpen, setSplitBillingOpen] = useState(false);
  const [shiftClosingOpen, setShiftClosingOpen] = useState(false);
  const [receiptData, setReceiptData] = useState<ReceiptData | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [couponCode, setCouponCode] = useState('');
  const [couponLoading, setCouponLoading] = useState(false);
  const [couponError, setCouponError] = useState<string | null>(null);

  // Keyboard shortcuts
  const handleHold = () => {
    if (getItemCount() > 0) {
      holdCurrentOrder(selectedCustomer?.name);
      showToast('Order held', 'info');
    }
  };

  const shortcuts = useMemo(() => ({
    'f1': () => {
      const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
      searchInput?.focus();
    },
    'f2': () => {
      if (getItemCount() > 0 && !paymentModalOpen) setPaymentModalOpen(true);
    },
    'f3': () => {
      if (getItemCount() > 0) handleHold();
    },
    'f4': () => {
      if (getItemCount() > 0) clearCart();
    },
    'escape': () => {
      setPaymentModalOpen(false);
      setReceiptData(null);
    },
  }), [getItemCount, paymentModalOpen, clearCart]);
  useKeyboardShortcuts(shortcuts);

  const handleAddToCart = useCallback((menuItem: MenuItem) => {
    addItem({
      menuItemId: menuItem.id,
      name: menuItem.name,
      quantity: 1,
      unitPrice: Number(menuItem.base_price),
      itemName: menuItem.name,
      itemCode: menuItem.item_code || '',
      categoryId: menuItem.category_id,
    });
    setSelectedItemId(menuItem.id);
  }, [addItem]);

  const handleRemoveItem = useCallback((itemId: string) => {
    removeItem(itemId);
    if (selectedItemId === itemId) setSelectedItemId(null);
  }, [removeItem, selectedItemId]);

  const handleUpdateQuantity = useCallback((itemId: string, quantity: number) => {
    if (quantity <= 0) {
      handleRemoveItem(itemId);
    } else {
      updateItemQuantity(itemId, quantity);
    }
  }, [updateItemQuantity, handleRemoveItem]);

  const handleNumPad = useCallback((num: number) => {
    if (num === -1) {
      if (selectedItemId) handleRemoveItem(selectedItemId);
      return;
    }
    if (num === -2 || num === 0) return;

    const targetId = selectedItemId || currentOrder.items[currentOrder.items.length - 1]?.menuItemId;
    if (targetId) {
      updateItemQuantity(targetId, num);
    }
  }, [selectedItemId, currentOrder.items, updateItemQuantity, handleRemoveItem]);

  const handleCheckout = () => {
    if (getItemCount() > 0) {
      setPaymentModalOpen(true);
    }
  };

  const handlePaymentComplete = async (paymentMethod: string) => {
    // CRITICAL: Capture receipt data BEFORE payment clears the cart
    const receiptSnapshot = {
      id: Date.now().toString(),
      items: currentOrder.items.map(item => ({
        name: item.name,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        total: item.unitPrice * item.quantity,
      })),
      subtotal: getSubtotal(),
      discount: getDiscount(),
      discountLabel: discountLabel,
      tax: getTax(),
      total: getTotal(),
      paymentMethod,
      tableId: selectedTableId,
    };

    const success = await completePayment(paymentMethod);
    if (success) {
      setPaymentModalOpen(false);
      showToast('Payment successful!', 'success');
      setReceiptData(receiptSnapshot);
    } else {
      showToast('Payment failed. Please try again.', 'error');
    }
  };

  const handleCloseReceipt = () => {
    setReceiptData(null);
  };

  const handleApplyCoupon = async () => {
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    setCouponError(null);
    try {
      const res = await couponsApi.validate(couponCode.trim(), getSubtotal());
      if (res.data.valid) {
        setDiscount(res.data.discount, couponCode.trim().toUpperCase());
        showToast(`Coupon applied! ₹${res.data.discount.toFixed(2)} off`, 'success');
      } else {
        setCouponError('Invalid coupon');
      }
    } catch {
      setCouponError('Invalid coupon');
    } finally {
      setCouponLoading(false);
    }
  };

  const handleRemoveDiscount = () => {
    setDiscount(0, '');
    setCouponCode('');
    setCouponError(null);
  };

  const handleManualDiscount = () => {
    const input = prompt('Enter discount amount (₹):');
    if (input) {
      const amount = parseFloat(input);
      if (!isNaN(amount) && amount > 0) {
        setDiscount(amount, 'Manual');
      }
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h1 className="text-lg font-bold text-gray-800">KitchenOS</h1>
        </div>

        <div className="flex-1 overflow-auto">
          <div className="border-b">
            <div className="px-4 pt-3 pb-1">
              <h3 className="font-semibold text-sm">Customer</h3>
            </div>
            <CustomerLookup
              selectedCustomer={selectedCustomer}
              onSelect={setSelectedCustomer}
            />
          </div>
          <TableSelection
            selectedTable={selectedTableId}
            onTableSelect={setSelectedTable}
          />
        </div>

        {/* Coupon Input */}
        {getItemCount() > 0 && !discountAmount && (
          <div className="p-3 border-b">
            <div className="flex gap-1">
              <input
                type="text"
                placeholder="Coupon code"
                value={couponCode}
                onChange={e => setCouponCode(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && handleApplyCoupon()}
                className="flex-1 px-2 py-1 border rounded text-sm"
              />
              <button
                onClick={handleApplyCoupon}
                disabled={couponLoading || !couponCode.trim()}
                className="px-2 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 disabled:opacity-50"
              >
                {couponLoading ? '...' : 'Apply'}
              </button>
              <button
                onClick={handleManualDiscount}
                className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                title="Manual discount"
              >
                ₹
              </button>
            </div>
            {couponError && <div className="text-xs text-red-500 mt-1">{couponError}</div>}
          </div>
        )}

        {/* Order Summary */}
        <div className="p-4 border-t">
          <div className="space-y-1 text-sm mb-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Items:</span>
              <span className="font-medium">{getItemCount()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal:</span>
              <span className="font-medium">₹{getSubtotal().toFixed(2)}</span>
            </div>
            {discountAmount > 0 && (
              <div className="flex justify-between text-green-600">
                <span className="flex items-center gap-1">
                  Discount ({discountLabel})
                  <button onClick={handleRemoveDiscount} className="text-xs text-red-400 hover:text-red-600">
                    x
                  </button>
                </span>
                <span className="font-medium">-₹{getDiscount().toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600">Tax (18%):</span>
              <span className="font-medium">₹{getTax().toFixed(2)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t">
              <span className="font-bold">Total:</span>
              <span className="font-bold text-lg">₹{getTotal().toFixed(2)}</span>
            </div>
          </div>

          {error && (
            <div className="mb-2 p-2 bg-red-50 text-red-600 text-sm rounded">
              {error}
            </div>
          )}

          <button
            onClick={handleCheckout}
            disabled={getItemCount() === 0 || isSubmitting}
            className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? 'Processing...' : `Checkout ₹${getTotal().toFixed(2)}`}
          </button>

          <div className="flex gap-2 mt-2">
            <button
              onClick={handleHold}
              disabled={getItemCount() === 0}
              className="flex-1 bg-yellow-500 text-white py-2 rounded hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              Hold (F3)
            </button>
            <button
              onClick={() => setSplitBillingOpen(true)}
              disabled={getItemCount() === 0}
              className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              Split
            </button>
            <button
              onClick={clearCart}
              disabled={getItemCount() === 0}
              className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Held Orders */}
        {heldOrders.length > 0 && (
          <div className="border-t p-3">
            <h3 className="font-semibold text-sm mb-2 text-gray-600">Held Orders ({heldOrders.length})</h3>
            <div className="space-y-1 max-h-40 overflow-auto">
              {heldOrders.map(held => (
                <div
                  key={held.id}
                  className="flex items-center justify-between p-2 bg-yellow-50 rounded border border-yellow-200 text-sm"
                >
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">
                      {held.customerName || `Order ${held.id.slice(-4)}`}
                    </div>
                    <div className="text-xs text-gray-500">
                      {held.items.length} items · ₹{held.items.reduce((s, i) => s + i.unitPrice * i.quantity, 0).toFixed(0)}
                      {held.tableId && ` · T${held.tableId}`}
                    </div>
                  </div>
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={() => {
                        resumeOrder(held.id);
                        showToast('Order resumed', 'info');
                      }}
                      className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
                    >
                      Resume
                    </button>
                    <button
                      onClick={() => removeHeldOrder(held.id)}
                      className="px-1 py-1 text-red-400 hover:text-red-600 text-xs"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b px-6 py-2 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-semibold">POS Terminal</h2>
            <div className="hidden lg:flex items-center gap-1 text-xs text-gray-400">
              <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px]">F1</kbd><span>Search</span>
              <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F2</kbd><span>Pay</span>
              <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F3</kbd><span>Hold</span>
              <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F4</kbd><span>Clear</span>
              <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">Esc</kbd><span>Close</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-500">{currentOrder.items.length} item(s)</span>
            <LanguageSwitcher />
            <button
              onClick={() => setShiftClosingOpen(true)}
              className="text-orange-500 hover:text-orange-700 text-sm font-medium"
            >
              Z-Report
            </button>
            <button
              onClick={logout}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              Logout
            </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Menu */}
          <div className="flex-1 overflow-auto p-6">
            <MenuGrid onItemSelect={handleAddToCart} />
          </div>

          {/* Cart + NumPad */}
          <div className="w-80 border-l bg-gray-50 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-auto p-4">
              <Cart
                items={currentOrder.items}
                onRemove={handleRemoveItem}
                onUpdateQuantity={handleUpdateQuantity}
              />
            </div>
            <div className="p-4 border-t">
              <NumPad onQuantitySelect={handleNumPad} />
            </div>
          </div>
        </div>
      </main>

      {/* Payment Modal */}
      <PaymentModal
        open={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        onComplete={handlePaymentComplete}
        totalAmount={getTotal()}
        isSubmitting={isSubmitting}
      />

      {/* Receipt Modal */}
      <ReceiptModal
        open={!!receiptData}
        onClose={handleCloseReceipt}
        order={receiptData}
      />

      {/* Shift Closing */}
      <ShiftClosing
        open={shiftClosingOpen}
        onClose={() => setShiftClosingOpen(false)}
      />

      {/* Split Billing */}
      <SplitBilling
        open={splitBillingOpen}
        onClose={() => setSplitBillingOpen(false)}
        items={currentOrder.items.map(item => ({
          name: item.name,
          quantity: item.quantity,
          unitPrice: item.unitPrice,
          total: item.unitPrice * item.quantity,
        }))}
        totalAmount={getTotal()}
        onConfirm={(splits) => {
          showToast(`Bill split into ${splits.length} parts`, 'success');
          // Process first split payment, rest can be paid individually
          setSplitBillingOpen(false);
        }}
      />
    </div>
  );
};

export default POSPage;
