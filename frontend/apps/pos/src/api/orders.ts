import apiClient from './client';

export interface OrderItemCreate {
  menu_item_id: string;
  item_name: string;
  item_code?: string;
  quantity: number;
  unit_price: number;
  tax_amount?: number;
  discount_amount?: number;
  total?: number;
  variant_id?: string;
  variant_name?: string;
  modifiers?: Record<string, unknown>[];
  cooking_instructions?: string;
}

export interface OrderCreate {
  order_type: string;
  table_id?: string;
  branch_id?: string;
  customer_id?: string;
  customer_name?: string;
  customer_phone?: string;
  special_instructions?: string;
  source?: string;
  items: OrderItemCreate[];
  discount_amount?: number;
}

export interface OrderItem {
  id: string;
  menu_item_id: string;
  item_name: string;
  item_code: string | null;
  quantity: number;
  unit_price: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  variant_id: string | null;
  variant_name: string | null;
  modifiers: Record<string, unknown>[];
  cooking_instructions: string | null;
  prep_status: string;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  tenant_id: string;
  branch_id: string;
  table_id: string | null;
  order_type: string;
  status: string;
  customer_id: string | null;
  customer_name: string | null;
  customer_phone: string | null;
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  tip_amount: number;
  total: number;
  payment_status: string;
  special_instructions: string | null;
  source: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string | null;
}

export const ordersApi = {
  create: (order: OrderCreate) =>
    apiClient.post<Order>('/orders/', order),

  getAll: (params?: { branch_id?: string; status?: string; skip?: number; limit?: number }) =>
    apiClient.get<Order[]>('/orders/', { params }),

  get: (orderId: string) =>
    apiClient.get<Order>(`/orders/${orderId}`),

  update: (orderId: string, data: Partial<OrderCreate & { status: string; payment_status: string }>) =>
    apiClient.put<Order>(`/orders/${orderId}`, data),

  delete: (orderId: string) =>
    apiClient.delete(`/orders/${orderId}`),

  updateStatus: (orderId: string, status: string) =>
    apiClient.put<Order>(`/orders/${orderId}/status`, null, { params: { status } }),

  getActive: (branchId?: string) =>
    apiClient.get<Order[]>('/orders/active/', {
      params: branchId ? { branch_id: branchId } : {},
    }),
};
