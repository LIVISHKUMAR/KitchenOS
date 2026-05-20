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
import { POSSidebar } from '../components/pos/POSSidebar';
import { POSHeader } from '../components/pos/POSHeader';
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
    currentOrder, selectedTableId, isSubmitting, error,
    discountAmount, discountLabel, heldOrders,
    addItem, updateItemQuantity, removeItem, clearCart,
    setSelectedTable, setDiscount, completePayment,
    holdCurrentOrder, resumeOrder, removeHeldOrder,
    getSubtotal, getDiscount, getTax, getTotal, getItemCount,
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

  const handleHold = useCallback(() => {
    if (getItemCount() > 0) {
      holdCurrentOrder(selectedCustomer?.name);
      showToast('Order held', 'info');
    }
  }, [getItemCount, holdCurrentOrder, selectedCustomer, showToast]);

  const shortcuts = useMemo(() => ({
    'f1': () => { document.querySelector<HTMLInputElement>('[data-search-input]')?.focus(); },
    'f2': () => { if (getItemCount() > 0 && !paymentModalOpen) setPaymentModalOpen(true); },
    'f3': () => { if (getItemCount() > 0) handleHold(); },
    'f4': () => { if (getItemCount() > 0) clearCart(); },
    'escape': () => { setPaymentModalOpen(false); setReceiptData(null); },
  }), [getItemCount, paymentModalOpen, clearCart, handleHold]);
  useKeyboardShortcuts(shortcuts);

  const handleAddToCart = useCallback((menuItem: MenuItem) => {
    addItem({
      menuItemId: menuItem.id, name: menuItem.name, quantity: 1,
      unitPrice: Number(menuItem.base_price), itemName: menuItem.name,
      itemCode: menuItem.item_code || '', categoryId: menuItem.category_id,
    });
    setSelectedItemId(menuItem.id);
  }, [addItem]);

  const handleRemoveItem = useCallback((itemId: string) => {
    removeItem(itemId);
    if (selectedItemId === itemId) setSelectedItemId(null);
  }, [removeItem, selectedItemId]);

  const handleUpdateQuantity = useCallback((itemId: string, quantity: number) => {
    if (quantity <= 0) handleRemoveItem(itemId);
    else updateItemQuantity(itemId, quantity);
  }, [updateItemQuantity, handleRemoveItem]);

  const handleNumPad = useCallback((num: number) => {
    if (num === -1) { if (selectedItemId) handleRemoveItem(selectedItemId); return; }
    if (num === -2 || num === 0) return;
    const targetId = selectedItemId || currentOrder.items[currentOrder.items.length - 1]?.menuItemId;
    if (targetId) updateItemQuantity(targetId, num);
  }, [selectedItemId, currentOrder.items, updateItemQuantity, handleRemoveItem]);

  const handlePaymentComplete = useCallback(async (paymentMethod: string) => {
    const receiptSnapshot = {
      id: Date.now().toString(),
      items: currentOrder.items.map(item => ({ name: item.name, quantity: item.quantity, unitPrice: item.unitPrice, total: item.unitPrice * item.quantity })),
      subtotal: getSubtotal(), discount: getDiscount(), discountLabel, tax: getTax(), total: getTotal(),
      paymentMethod, tableId: selectedTableId,
    };
    const success = await completePayment(paymentMethod);
    if (success) {
      setPaymentModalOpen(false);
      showToast('Payment successful!', 'success');
      setReceiptData(receiptSnapshot);
    } else {
      showToast('Payment failed. Please try again.', 'error');
    }
  }, [currentOrder.items, discountLabel, selectedTableId, completePayment, getSubtotal, getDiscount, getTax, getTotal, showToast]);

  const handleApplyCoupon = useCallback(async () => {
    if (!couponCode.trim()) return;
    setCouponLoading(true); setCouponError(null);
    try {
      const res = await couponsApi.validate(couponCode.trim(), getSubtotal());
      if (res.data.valid) {
        setDiscount(res.data.discount, couponCode.trim().toUpperCase());
        showToast(`Coupon applied! ₹${res.data.discount.toFixed(2)} off`, 'success');
      } else { setCouponError('Invalid coupon'); }
    } catch { setCouponError('Invalid coupon'); } finally { setCouponLoading(false); }
  }, [couponCode, getSubtotal, setDiscount, showToast]);

  const handleResumeOrder = useCallback((id: string) => {
    resumeOrder(id); showToast('Order resumed', 'info');
  }, [resumeOrder, showToast]);

  return (
    <div className="flex h-screen bg-gray-50">
      <POSSidebar
        selectedCustomer={selectedCustomer} onSelectCustomer={setSelectedCustomer}
        selectedTableId={selectedTableId} onSelectTable={setSelectedTable}
        itemCount={getItemCount()} subtotal={getSubtotal()}
        discountAmount={discountAmount} discountLabel={discountLabel}
        discount={getDiscount()} tax={getTax()} total={getTotal()}
        error={error} isSubmitting={isSubmitting}
        couponCode={couponCode} setCouponCode={setCouponCode}
        couponLoading={couponLoading} couponError={couponError}
        onApplyCoupon={handleApplyCoupon}
        onRemoveDiscount={() => { setDiscount(0, ''); setCouponCode(''); setCouponError(null); }}
        onManualDiscount={() => { const input = prompt('Enter discount amount (₹):'); if (input) { const amount = parseFloat(input); if (!isNaN(amount) && amount > 0) setDiscount(amount, 'Manual'); } }}
        onCheckout={() => { if (getItemCount() > 0) setPaymentModalOpen(true); }}
        onHold={handleHold} onSplit={() => setSplitBillingOpen(true)} onClear={clearCart}
        heldOrders={heldOrders} onResumeOrder={handleResumeOrder} onRemoveHeldOrder={removeHeldOrder}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
        <POSHeader itemCount={currentOrder.items.length} onShiftClosing={() => setShiftClosingOpen(true)} onLogout={logout} />

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 overflow-auto p-6">
            <MenuGrid onItemSelect={handleAddToCart} />
          </div>
          <div className="w-80 border-l bg-gray-50 flex flex-col overflow-hidden">
            <div className="flex-1 overflow-auto p-4">
              <Cart items={currentOrder.items} onRemove={handleRemoveItem} onUpdateQuantity={handleUpdateQuantity} />
            </div>
            <div className="p-4 border-t">
              <NumPad onQuantitySelect={handleNumPad} />
            </div>
          </div>
        </div>
      </main>

      <PaymentModal open={paymentModalOpen} onClose={() => setPaymentModalOpen(false)} onComplete={handlePaymentComplete} totalAmount={getTotal()} isSubmitting={isSubmitting} />
      <ReceiptModal open={!!receiptData} onClose={() => setReceiptData(null)} order={receiptData} />
      <ShiftClosing open={shiftClosingOpen} onClose={() => setShiftClosingOpen(false)} />
      <SplitBilling open={splitBillingOpen} onClose={() => setSplitBillingOpen(false)} items={currentOrder.items.map(item => ({ name: item.name, quantity: item.quantity, unitPrice: item.unitPrice, total: item.unitPrice * item.quantity }))} totalAmount={getTotal()} onConfirm={(splits) => { showToast(`Bill split into ${splits.length} parts`, 'success'); setSplitBillingOpen(false); }} />
    </div>
  );
};

export default POSPage;
