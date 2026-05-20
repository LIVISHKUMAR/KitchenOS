import apiClient from './client';

export interface PaymentCreate {
  order_id: string;
  amount: number;
  payment_method: string;
  gateway?: string;
  transaction_id?: string;
  idempotency_key: string;
  payment_metadata?: Record<string, unknown>;
}

export interface Payment {
  id: string;
  order_id: string;
  tenant_id: string;
  branch_id: string;
  amount: number;
  payment_method: string;
  status: string;
  transaction_id: string | null;
  idempotency_key: string;
  processed_at: string | null;
  created_at: string;
}

export interface RefundRequest {
  payment_id: string;
  amount: number;
  reason: string;
}

export const paymentsApi = {
  create: (payment: PaymentCreate) =>
    apiClient.post<Payment>('/payments/', payment),

  get: (paymentId: string) =>
    apiClient.get<Payment>(`/payments/${paymentId}`),

  getByOrder: (orderId: string) =>
    apiClient.get<Payment[]>(`/payments/order/${orderId}`),

  refund: (data: RefundRequest) =>
    apiClient.post('/payments/refund', data),

  void: (paymentId: string, reason: string) =>
    apiClient.post(`/payments/${paymentId}/void`, { reason }),
};
