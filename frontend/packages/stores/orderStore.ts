import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CartItem {
  id: string;
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  variants?: { id: string; name: string; price: number }[];
  modifiers?: { id: string; name: string; price: number }[];
  notes?: string;
}

interface OrderState {
  // Current order
  currentOrder: {
    id?: string;
    orderNumber?: string;
    type: 'dine_in' | 'takeaway' | 'delivery';
    tableId?: string;
    items: CartItem[];
    customerId?: string;
    notes?: string;
  };
  
  // Actions
  addItem: (item: CartItem) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  updateItemModifiers: (itemId: string, modifiers: CartItem['modifiers']) => void;
  setOrderType: (type: OrderState['currentOrder']['type']) => void;
  setTableId: (tableId: string) => void;
  setCustomerId: (customerId: string) => void;
  clearCart: () => void;
  
  // Computed
  getSubtotal: () => number;
  getTax: () => number;
  getTotal: () => number;
  getItemCount: () => number;
}

export const useOrderStore = create<OrderState>()(
  persist(
    (set, get) => ({
      currentOrder: {
        type: 'dine_in',
        items: [],
      },
      
      addItem: (item) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: [...state.currentOrder.items, { ...item, id: crypto.randomUUID() }]
        }
      })),
      
      updateItemQuantity: (itemId, quantity) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: state.currentOrder.items.map(item =>
            item.id === itemId ? { ...item, quantity } : item
          )
        }
      })),
      
      removeItem: (itemId) => set((state) => ({
        currentOrder: {
          ...state.currentOrder,
          items: state.currentOrder.items.filter(item => item.id !== itemId)
        }
      })),
      
      setOrderType: (type) => set((state) => ({
        currentOrder: { ...state.currentOrder, type }
      })),
      
      setTableId: (tableId) => set((state) => ({
        currentOrder: { ...state.currentOrder, tableId }
      })),
      
      setCustomerId: (customerId) => set((state) => ({
        currentOrder: { ...state.currentOrder, customerId }
      })),
      
      clearCart: () => set({
        currentOrder: { type: 'dine_in', items: [] }
      }),
      
      getSubtotal: () => {
        const items = get().currentOrder.items;
        return items.reduce((sum, item) => {
          const basePrice = item.unitPrice * item.quantity;
          const variantPrice = (item.variants || []).reduce((v, w) => v + w.price, 0) * item.quantity;
          const modPrice = (item.modifiers || []).reduce((m, n) => m + n.price, 0) * item.quantity;
          return sum + basePrice + variantPrice + modPrice;
        }, 0);
      },
      
      getTax: () => get().getSubtotal() * 0.18, // 18% GST
      getTotal: () => get().getSubtotal() + get().getTax(),
      getItemCount: () => get().currentOrder.items.reduce((sum, item) => sum + item.quantity, 0),
    }),
    { name: 'pos-order-store' }
  )
);