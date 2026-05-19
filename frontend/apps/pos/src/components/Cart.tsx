import React from 'react';
import { useOrderStore, type CartItem } from '../stores/orderStore';

interface CartProps {
  items: CartItem[];
  onRemove: (itemId: string) => void;
  onUpdateQuantity: (itemId: string, quantity: number) => void;
}

const Cart: React.FC<CartProps> = ({ items, onRemove, onUpdateQuantity }) => {
  const { getSubtotal, getTax, getTotal, getItemCount } = useOrderStore();

  if (getItemCount() === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-400 text-sm">Cart is empty</p>
        <p className="text-gray-400 text-xs mt-1">Select items from the menu</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Cart items */}
      <div className="space-y-2">
        {items.map(item => (
          <div
            key={item.menuItemId}
            className="bg-white rounded-lg shadow-sm p-3 flex items-center justify-between"
          >
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{item.itemName}</p>
              <p className="text-xs text-gray-500">
                ₹{item.unitPrice.toFixed(2)} x {item.quantity}
              </p>
            </div>
            <div className="flex items-center gap-2 ml-2">
              <button
                onClick={() => onUpdateQuantity(item.menuItemId, item.quantity - 1)}
                className="w-7 h-7 bg-gray-100 rounded hover:bg-gray-200 flex items-center justify-center text-gray-600 text-sm"
              >
                -
              </button>
              <span className="w-6 text-center text-sm font-medium">{item.quantity}</span>
              <button
                onClick={() => onUpdateQuantity(item.menuItemId, item.quantity + 1)}
                className="w-7 h-7 bg-gray-100 rounded hover:bg-gray-200 flex items-center justify-center text-gray-600 text-sm"
              >
                +
              </button>
              <button
                onClick={() => onRemove(item.menuItemId)}
                className="w-7 h-7 text-red-400 hover:text-red-600 hover:bg-red-50 rounded flex items-center justify-center text-sm"
              >
                x
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="bg-white rounded-lg shadow-sm p-3 space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Subtotal</span>
          <span>₹{getSubtotal().toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">GST (18%)</span>
          <span>₹{getTax().toFixed(2)}</span>
        </div>
        <div className="flex justify-between pt-2 border-t font-bold">
          <span>Total</span>
          <span>₹{getTotal().toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

export { Cart };
