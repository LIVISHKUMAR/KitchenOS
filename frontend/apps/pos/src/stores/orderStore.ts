import { create } from 'zustand';
import { ordersApi, paymentsApi, type OrderCreate, type OrderItemCreate } from '../api';

export interface CartItem {
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  itemName: string;
  itemCode: string;
  categoryId?: string;
}

interface OrderState {
  currentOrder: { items: CartItem[] };
  selectedTableId: string | null;
  orderType: 'dine_in' | 'takeaway' | 'delivery';
  isSubmitting: boolean;
  lastOrderId: string | null;
  error: string | null;

  // Cart actions
  addItem: (item: CartItem) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  clearCart: () => void;

  // Order actions
  setSelectedTable: (tableId: string | null) => void;
  setOrderType: (type: 'dine_in' | 'takeaway' | 'delivery') => void;
  submitOrder: (branchId?: string) => Promise<string | null>;
  completePayment: (paymentMethod: string, branchId?: string) => Promise<boolean>;

  // Computed
  getSubtotal: () => number;
  getTax: () => number;
  getTotal: () => number;
  getItemCount: () => number;
}

export const useOrderStore = create<OrderState>((set, get) => ({
  currentOrder: { items: [] },
  selectedTableId: null,
  orderType: 'dine_in',
  isSubmitting: false,
  lastOrderId: null,
  error: null,

  addItem: (item) => set((state) => {
    const existing = state.currentOrder.items.find(i => i.menuItemId === item.menuItemId);
    if (existing) {
      return {
        currentOrder: {
          items: state.currentOrder.items.map(i =>
            i.menuItemId === item.menuItemId
              ? { ...i, quantity: i.quantity + item.quantity }
              : i
          ),
        },
      };
    }
    return { currentOrder: { items: [...state.currentOrder.items, item] } };
  }),

  updateItemQuantity: (itemId, quantity) => set((state) => ({
    currentOrder: {
      items: state.currentOrder.items.map(i =>
        i.menuItemId === itemId ? { ...i, quantity } : i
      ),
    },
  })),

  removeItem: (itemId) => set((state) => ({
    currentOrder: {
      items: state.currentOrder.items.filter(i => i.menuItemId !== itemId),
    },
  })),

  clearCart: () => set({
    currentOrder: { items: [] },
    lastOrderId: null,
    error: null,
  }),

  setSelectedTable: (tableId) => set({ selectedTableId: tableId }),
  setOrderType: (type) => set({ orderType: type }),

  submitOrder: async (branchId) => {
    const state = get();
    if (state.currentOrder.items.length === 0) return null;

    set({ isSubmitting: true, error: null });

    try {
      const orderItems: OrderItemCreate[] = state.currentOrder.items.map(item => ({
        menu_item_id: item.menuItemId,
        item_name: item.itemName,
        item_code: item.itemCode,
        quantity: item.quantity,
        unit_price: item.unitPrice,
        total: item.unitPrice * item.quantity,
      }));

      const orderData: OrderCreate = {
        order_type: state.orderType,
        table_id: state.selectedTableId || undefined,
        branch_id: branchId,
        items: orderItems,
        source: 'pos',
      };

      const response = await ordersApi.create(orderData);
      set({ lastOrderId: response.data.id, isSubmitting: false });
      return response.data.id;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create order';
      set({ error: message, isSubmitting: false });
      return null;
    }
  },

  completePayment: async (paymentMethod, branchId) => {
    const state = get();

    // If no order submitted yet, submit first
    let orderId = state.lastOrderId;
    if (!orderId) {
      orderId = await get().submitOrder(branchId);
      if (!orderId) return false;
    }

    try {
      const idempotencyKey = `pay-${orderId}-${Date.now()}`;
      await paymentsApi.create({
        order_id: orderId,
        amount: get().getTotal(),
        payment_method: paymentMethod,
        idempotency_key: idempotencyKey,
      });

      // Clear cart after successful payment
      set({
        currentOrder: { items: [] },
        lastOrderId: null,
        isSubmitting: false,
      });
      return true;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Payment failed';
      set({ error: message, isSubmitting: false });
      return false;
    }
  },

  getSubtotal: () => get().currentOrder.items.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity, 0
  ),

  getTax: () => get().getSubtotal() * 0.18,

  getTotal: () => get().getSubtotal() + get().getTax(),

  getItemCount: () => get().currentOrder.items.reduce(
    (sum, item) => sum + item.quantity, 0
  ),
}));
