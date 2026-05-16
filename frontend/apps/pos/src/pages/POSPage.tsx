import React, { useState } from 'react';
import { useOrderStore } from '../../stores/orderStore';
import { MenuGrid } from '../../components/MenuGrid';
import { Cart } from '../../components/Cart';
import { NumPad } from '../../components/NumPad';
import { PaymentModal } from '../../components/PaymentModal';
import { TableSelection } from '../../components/TableSelection';

const POSPage = () => {
  const { 
    currentOrder, 
    addItem, 
    updateItemQuantity, 
    removeItem, 
    clearCart,
    getSubtotal,
    getTax,
    getTotal,
    getItemCount
  } = useOrderStore();
  
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [selectedTable, setSelectedTable] = useState(null);

  const handleAddToCart = (menuItem) => {
    addItem({
      menuItemId: menuItem.id,
      name: menuItem.name,
      quantity: 1,
      unitPrice: menuItem.base_price,
      itemName: menuItem.name,
      itemCode: menuItem.item_code,
    });
  };

  const handleRemoveItem = (itemId) => {
    removeItem(itemId);
  };

  const handleUpdateQuantity = (itemId, quantity) => {
    if (quantity <= 0) {
      handleRemoveItem(itemId);
    } else {
      updateItemQuantity(itemId, quantity);
    }
  };

  const handleCheckout = () => {
    if (getItemCount() > 0) {
      setPaymentModalOpen(true);
    }
  };

  const handlePaymentComplete = () => {
    clearCart();
    setPaymentModalOpen(false);
    // In a real app, we would create the order via API
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r">
        <TableSelection 
          selectedTable={selectedTable} 
          onTableSelect={setSelectedTable} 
        />
        
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
          <div className="space-y-2">
            <div className="text-sm">
              <span>Items:</span> <span className="ml-2">{getItemCount()}</span>
            </div>
            <div className="text-sm">
              <span>Subtotal:</span> <span className="ml-2">${getSubtotal().toFixed(2)}</span>
            </div>
            <div className="text-sm">
              <span>Tax:</span> <span className="ml-2">${getTax().toFixed(2)}</span>
            </div>
            <div className="text-lg font-bold">
              <span>Total:</span> <span className="ml-2">${getTotal().toFixed(2)}</span>
            </div>
          </div>
          
          {getItemCount() > 0 && (
            <button 
              onClick={handleCheckout}
              className="w-full mt-4 bg-green-500 text-white py-2 rounded hover:bg-green-600"
            >
              Checkout
            </button>
          )}
          
          <button 
            onClick={clearCart}
            className="w-full mt-2 bg-red-500 text-white py-2 rounded hover:bg-red-600"
          >
            Clear Cart
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6">
        <header className="mb-6">
          <h1 className="text-2xl font-bold">KitchenOS Terminal</h1>
          <p className="text-gray-600">Table: {selectedTable || 'Not selected'}</p>
        </header>

        <div className="grid grid-cols-3 gap-6">
          {/* Menu Grid */}
          <section className="col-span-2">
            <MenuGrid onItemSelect={handleAddToCart} />
          </section>

          {/* Cart */}
          <section>
            <Cart 
              items={currentOrder.items} 
              onRemove={handleRemoveItem}
              onUpdateQuantity={handleUpdateQuantity}
            />
          </section>
        </div>

        {/* Numpad */}
        <div className="mt-6">
          <NumPad 
            onQuantitySelect={(quantity) => {
              // Apply quantity to last added item or selected item
              // This is a simplified implementation
            }} 
          />
        </div>
      </main>

      {/* Payment Modal */}
      <PaymentModal 
        open={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        onComplete={handlePaymentComplete}
        totalAmount={getTotal()}
      />
    </div>
  );
};

export default POSPage;
