import apiClient from './client';

export interface Customer {
  id: string;
  name: string;
  email: string | null;
  phone: string;
  loyalty_points: number;
  wallet_balance: number;
  total_orders: number;
  total_spent: number;
  customer_type: string;
  membership_tier: string | null;
}

export const customersApi = {
  search: (query: string) =>
    apiClient.get<Customer[]>('/customers/', { params: { search: query } }),

  getByPhone: (phone: string) =>
    apiClient.get<Customer | null>(`/customers/phone/${phone}`),

  getById: (customerId: string) =>
    apiClient.get<Customer>(`/customers/${customerId}`),
};
