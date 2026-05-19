import { create } from 'zustand'

interface CartItem {
  id: string
  name: string
  price: number
  quantity: number
  is_veg: boolean
}

interface CartStore {
  items: CartItem[]
  addItem: (item: Omit<CartItem, 'quantity'>) => void
  removeItem: (id: string) => void
  updateQuantity: (id: string, quantity: number) => void
  clearCart: () => void
  getTotal: () => number
  getItemCount: () => number
}

export const useCartStore = create<CartStore>((set, get) => ({
  items: [],

  addItem: (item) => set((state) => {
    const existing = state.items.find(i => i.id === item.id)
    if (existing) {
      return {
        items: state.items.map(i =>
          i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
        ),
      }
    }
    return { items: [...state.items, { ...item, quantity: 1 }] }
  }),

  removeItem: (id) => set((state) => ({
    items: state.items.filter(i => i.id !== id),
  })),

  updateQuantity: (id, quantity) => set((state) => ({
    items: quantity <= 0
      ? state.items.filter(i => i.id !== id)
      : state.items.map(i => i.id === id ? { ...i, quantity } : i),
  })),

  clearCart: () => set({ items: [] }),

  getTotal: () => {
    const subtotal = get().items.reduce((sum, item) => sum + item.price * item.quantity, 0)
    return subtotal + subtotal * 0.18 // Add 18% GST
  },

  getItemCount: () => get().items.reduce((sum, item) => sum + item.quantity, 0),
}))
