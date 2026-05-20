import apiClient from './client';

export interface Coupon {
  id: string;
  code: string;
  description: string;
  discount_type: 'flat' | 'percentage';
  discount_value: number;
  min_order_value: number;
  max_discount: number | null;
  is_active: boolean;
}

export const couponsApi = {
  validate: (code: string, orderTotal: number) =>
    apiClient.post<{ valid: boolean; discount: number; coupon: Coupon }>('/coupons/validate', {
      code,
      order_total: orderTotal,
    }),

  list: () => apiClient.get<Coupon[]>('/coupons/'),
};
