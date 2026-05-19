import React, { useState, useCallback } from 'react';
import { useOrderStore } from '../stores/orderStore';
import { MenuGrid } from '../components/MenuGrid';
import { Cart } from '../components/Cart';
import { NumPad } from '../components/NumPad';
import { PaymentModal } from '../components/PaymentModal';
import { TableSelection } from '../components/TableSelection';
import type { MenuItem } from '../api';

const POSPage = () => {
  const {
    currentOrder,
    selectedTableId,
    isSubmitting,
    error,
    addItem,
    updateItemQuantity,
    removeItem,
    clearCart,
    setSelectedTable,
    completePayment,
    getSubtotal,
    getTax,
    getTotal,
    getItemCount,
  } = useOrderStore();

  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

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
      // Clear selected item
      if (selectedItemId) handleRemoveItem(selectedItemId);
      return;
    }
    if (num === -2 || num === 0) return; // OK or 0 — no-op for now

    // Set quantity of selected item (or last item)
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
    const success = await completePayment(paymentMethod);
    if (success) {
      setPaymentModalOpen(false);
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
          <TableSelection
            selectedTable={selectedTableId}
            onTableSelect={setSelectedTable}
          />
        </div>

        {/* Order Summary */}
        <div className="p-4 border-t">
          <div className="space-y-1 text-sm mb-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Table:</span>
              <span className="font-medium">{selectedTableId ? `#${selectedTableId}` : 'None'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Items:</span>
              <span className="font-medium">{getItemCount()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal:</span>
              <span className="font-medium">₹{getSubtotal().toFixed(2)}</span>
            </div>
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

          <button
            onClick={clearCart}
            disabled={getItemCount() === 0}
            className="w-full mt-2 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            Clear Cart
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">POS Terminal</h2>
          </div>
          <div className="text-sm text-gray-500">
            {currentOrder.items.length} item(s) in cart
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
    </div>
  );
};

export default POSPage;
