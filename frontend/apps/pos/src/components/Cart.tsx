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
      <div className="text-center py-8" role="status" aria-label="Cart is empty">
        <p className="text-gray-400 text-sm">Cart is empty</p>
        <p className="text-gray-400 text-xs mt-1">Select items from the menu</p>
      </div>
    );
  }

  return (
    <div className="space-y-3" role="region" aria-label="Shopping cart">
      {/* Cart items */}
      <div className="space-y-2" role="list" aria-label="Cart items">
        {items.map(item => (
          <div
            key={item.menuItemId}
            role="listitem"
            aria-label={`${item.itemName}, quantity ${item.quantity}, ₹${(item.unitPrice * item.quantity).toFixed(2)}`}
            className="bg-white rounded-lg shadow-sm p-3 flex items-center justify-between"
          >
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm truncate">{item.itemName}</p>
              <p className="text-xs text-gray-500">
                ₹{item.unitPrice.toFixed(2)} × {item.quantity}
              </p>
            </div>
            <div className="flex items-center gap-2 ml-2">
              <button
                onClick={() => onUpdateQuantity(item.menuItemId, item.quantity - 1)}
                aria-label={`Decrease ${item.itemName} quantity`}
                className="w-8 h-8 bg-gray-100 rounded-lg hover:bg-gray-200 flex items-center justify-center text-gray-600 text-sm font-medium transition-colors active:scale-95"
              >
                −
              </button>
              <span className="w-6 text-center text-sm font-medium" aria-live="polite" aria-atomic="true">
                {item.quantity}
              </span>
              <button
                onClick={() => onUpdateQuantity(item.menuItemId, item.quantity + 1)}
                aria-label={`Increase ${item.itemName} quantity`}
                className="w-8 h-8 bg-gray-100 rounded-lg hover:bg-gray-200 flex items-center justify-center text-gray-600 text-sm font-medium transition-colors active:scale-95"
              >
                +
              </button>
              <button
                onClick={() => onRemove(item.menuItemId)}
                aria-label={`Remove ${item.itemName} from cart`}
                className="w-8 h-8 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg flex items-center justify-center text-sm transition-colors active:scale-95"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Totals */}
      <div className="bg-white rounded-lg shadow-sm p-3 space-y-1 text-sm" aria-label="Order summary">
        <div className="flex justify-between">
          <span className="text-gray-600">Subtotal</span>
          <span aria-label={`Subtotal ₹${getSubtotal().toFixed(2)}`}>₹{getSubtotal().toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">GST (18%)</span>
          <span aria-label={`GST ₹${getTax().toFixed(2)}`}>₹{getTax().toFixed(2)}</span>
        </div>
        <div className="flex justify-between pt-2 border-t font-bold text-base">
          <span>Total</span>
          <span aria-live="polite" aria-atomic="true" aria-label={`Total ₹${getTotal().toFixed(2)}`}>
            ₹{getTotal().toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export { Cart };
