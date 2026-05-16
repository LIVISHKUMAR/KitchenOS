import React from 'react';
import { useOrderStore } from '../../stores/orderStore';

interface CartProps {
  onRemove: (itemId: string) => void;
  onUpdateQuantity: (itemId: string, quantity: number) => void;
}

const Cart: React.FC<CartProps> = ({ onRemove, onUpdateQuantity }) => {
  const { currentOrder, getSubtotal, getTax, getTotal, getItemCount } = useOrderStore();

  if (getItemCount() === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">Your cart is empty</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Your Cart</h3>
          <span className="text-sm text-gray-500">{getItemCount()} items</span>
        </div>
        <div className="space-y-3">
          {currentOrder.items.map(item => (
            <div key={item.id} className="flex items-center justify-between py-2 border-t">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  {(item.item_name.toLowerCase().includes('pizza') ? '🍕' : 
                    item.item_name.toLowerCase().includes('burger') ? '🍔' :
                    item.item_name.toLowerCase().includes('salad') ? '🥗' :
                    item.item_name.toLowerCase().includes('cake') ? '🎂' : '🥤')}
                </div>
                <div>
                  <p className="font-medium">{item.item_name}</p>
                  <p className="text-sm text-gray-500">₹{item.unit_price} x {item.quantity}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                  className="w-8 h-8 bg-gray-100 rounded hover:bg-gray-200 flex items-center justify-center text-gray-600"
                >
                  −
                </button>
                <span className="w-8 text-center">{item.quantity}</span>
                <button
                  onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                  className="w-8 h-8 bg-gray-100 rounded hover:bg-gray-200 flex items-center justify-center text-gray-600"
                >
                  +
                </button>
                <button
                  onClick={() => onRemove(item.id)}
                  className="text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium">Subtotal:</span>
          <span className="font-medium">₹{getSubtotal().toFixed(2)}</span>
        </div>
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium">Tax (18%):</span>
          <span className="font-medium">₹{getTax().toFixed(2)}</span>
        </div>
        <div className="flex items-center justify-between pt-3 border-t">
          <span className="text-xl font-bold">Total:</span>
          <span className="text-xl font-bold">₹{getTotal().toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

export { Cart };