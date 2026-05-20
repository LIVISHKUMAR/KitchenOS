import apiClient from './client';

export interface RazorpayOrder {
  order_id: string;
  amount: number;
  currency: string;
  receipt: string;
  status: string;
  key_id: string;
}

export const razorpayApi = {
  createOrder: (amount: number, receipt?: string) =>
    apiClient.post<RazorpayOrder>('/razorpay/create-order', { amount, receipt }),

  verify: (data: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) =>
    apiClient.post<{ verified: boolean; payment_id: string }>('/razorpay/verify', data),
};
