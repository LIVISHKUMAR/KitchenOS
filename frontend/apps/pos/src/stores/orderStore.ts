import { create } from 'zustand';
import { ordersApi, paymentsApi, type OrderCreate, type OrderItemCreate } from '../api';
import { useAuthStore } from './authStore';
import { syncEngine } from '../offline/sync';

export interface CartItem {
  menuItemId: string;
  name: string;
  quantity: number;
  unitPrice: number;
  itemName: string;
  itemCode: string;
  categoryId?: string;
}

interface HeldOrder {
  id: string;
  items: CartItem[];
  tableId: string | null;
  orderType: 'dine_in' | 'takeaway' | 'delivery';
  discountAmount: number;
  discountLabel: string;
  heldAt: number;
  customerName?: string;
}

interface OrderState {
  currentOrder: { items: CartItem[] };
  selectedTableId: string | null;
  orderType: 'dine_in' | 'takeaway' | 'delivery';
  isSubmitting: boolean;
  lastOrderId: string | null;
  error: string | null;
  discountAmount: number;
  discountLabel: string;
  heldOrders: HeldOrder[];

  // Cart actions
  addItem: (item: CartItem) => void;
  updateItemQuantity: (itemId: string, quantity: number) => void;
  removeItem: (itemId: string) => void;
  clearCart: () => void;

  // Order actions
  setSelectedTable: (tableId: string | null) => void;
  setOrderType: (type: 'dine_in' | 'takeaway' | 'delivery') => void;
  setDiscount: (amount: number, label: string) => void;
  submitOrder: () => Promise<string | null>;
  completePayment: (paymentMethod: string) => Promise<boolean>;

  // Hold/Resume actions
  holdCurrentOrder: (customerName?: string) => void;
  resumeOrder: (heldOrderId: string) => void;
  removeHeldOrder: (heldOrderId: string) => void;

  // Computed
  getSubtotal: () => number;
  getDiscount: () => number;
  getTax: () => number;
  getTotal: () => number;
  getItemCount: () => number;
}

// Load held orders from localStorage
function loadHeldOrders(): HeldOrder[] {
  try {
    const stored = localStorage.getItem('kitchenos_held_orders');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

// Save held orders to localStorage
function saveHeldOrders(orders: HeldOrder[]) {
  try {
    localStorage.setItem('kitchenos_held_orders', JSON.stringify(orders));
  } catch {
    // Ignore storage errors
  }
}

export const useOrderStore = create<OrderState>((set, get) => ({
  currentOrder: { items: [] },
  selectedTableId: null,
  orderType: 'dine_in',
  isSubmitting: false,
  lastOrderId: null,
  error: null,
  discountAmount: 0,
  discountLabel: '',
  heldOrders: loadHeldOrders(),

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
    discountAmount: 0,
    discountLabel: '',
  }),

  setSelectedTable: (tableId) => set({ selectedTableId: tableId }),
  setOrderType: (type) => set({ orderType: type }),
  setDiscount: (amount, label) => set({ discountAmount: amount, discountLabel: label }),

  holdCurrentOrder: (customerName?: string) => {
    const state = get();
    if (state.currentOrder.items.length === 0) return;

    const held: HeldOrder = {
      id: `held-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      items: [...state.currentOrder.items],
      tableId: state.selectedTableId,
      orderType: state.orderType,
      discountAmount: state.discountAmount,
      discountLabel: state.discountLabel,
      heldAt: Date.now(),
      customerName,
    };

    const newHeld = [...state.heldOrders, held];
    saveHeldOrders(newHeld);

    set({
      heldOrders: newHeld,
      currentOrder: { items: [] },
      selectedTableId: null,
      orderType: 'dine_in',
      lastOrderId: null,
      discountAmount: 0,
      discountLabel: '',
      error: null,
    });
  },

  resumeOrder: (heldOrderId: string) => {
    const state = get();
    const held = state.heldOrders.find(h => h.id === heldOrderId);
    if (!held) return;

    // If current cart has items, hold them first
    if (state.currentOrder.items.length > 0) {
      get().holdCurrentOrder();
    }

    const remaining = state.heldOrders.filter(h => h.id !== heldOrderId);
    saveHeldOrders(remaining);

    set({
      currentOrder: { items: held.items },
      selectedTableId: held.tableId,
      orderType: held.orderType,
      discountAmount: held.discountAmount,
      discountLabel: held.discountLabel,
      heldOrders: remaining,
      lastOrderId: null,
      error: null,
    });
  },

  removeHeldOrder: (heldOrderId: string) => {
    const newHeld = get().heldOrders.filter(h => h.id !== heldOrderId);
    saveHeldOrders(newHeld);
    set({ heldOrders: newHeld });
  },

  submitOrder: async () => {
    const state = get();
    if (state.currentOrder.items.length === 0) return null;

    const branchId = useAuthStore.getState().branchId || undefined;

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
        discount_amount: state.discountAmount > 0 ? state.discountAmount : undefined,
      };

      if (!navigator.onLine) {
        const offlineId = await syncEngine.queueOrder(orderData as unknown as Record<string, unknown>);
        set({ lastOrderId: offlineId, isSubmitting: false });
        return offlineId;
      }

      const response = await ordersApi.create(orderData);
      set({ lastOrderId: response.data.id, isSubmitting: false });
      return response.data.id;
    } catch (err: any) {
      if (!navigator.onLine || err.code === 'ERR_NETWORK') {
        const offlineId = await syncEngine.queueOrder(
          { items: state.currentOrder.items } as unknown as Record<string, unknown>
        );
        set({ lastOrderId: offlineId, isSubmitting: false });
        return offlineId;
      }
      const message = err.response?.data?.detail || err.message || 'Failed to create order';
      set({ error: message, isSubmitting: false });
      return null;
    }
  },

  completePayment: async (paymentMethod) => {
    const state = get();

    let orderId = state.lastOrderId;
    if (!orderId) {
      orderId = await get().submitOrder();
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

      set({
        currentOrder: { items: [] },
        lastOrderId: null,
        isSubmitting: false,
        discountAmount: 0,
        discountLabel: '',
      });
      return true;
    } catch (err: any) {
      const message = err.response?.data?.detail || err.message || 'Payment failed';
      set({ error: message, isSubmitting: false });
      return false;
    }
  },

  getSubtotal: () => get().currentOrder.items.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity, 0
  ),

  getDiscount: () => {
    const { discountAmount } = get();
    const subtotal = get().getSubtotal();
    return Math.min(discountAmount, subtotal);
  },

  getTax: () => {
    const afterDiscount = get().getSubtotal() - get().getDiscount();
    return afterDiscount * 0.18;
  },

  getTotal: () => {
    const afterDiscount = get().getSubtotal() - get().getDiscount();
    return afterDiscount + get().getTax();
  },

  getItemCount: () => get().currentOrder.items.reduce(
    (sum, item) => sum + item.quantity, 0
  ),
}));
