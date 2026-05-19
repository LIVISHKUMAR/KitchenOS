import apiClient from './client';

export interface MenuItem {
  id: string;
  name: string;
  description: string | null;
  item_code: string | null;
  base_price: number;
  is_veg: boolean;
  is_available: boolean;
  category_id: string;
  preparation_time_minutes: number;
  image_url: string | null;
}

export interface MenuCategory {
  id: string;
  name: string;
  description: string | null;
  display_order: number;
  is_active: boolean;
}

export const menuApi = {
  getCategories: (branchId?: string) =>
    apiClient.get<MenuCategory[]>('/menu/categories', {
      params: branchId ? { branch_id: branchId } : {},
    }),

  getItems: (branchId?: string, categoryId?: string) =>
    apiClient.get<MenuItem[]>('/menu/items', {
      params: {
        ...(branchId ? { branch_id: branchId } : {}),
        ...(categoryId ? { category_id: categoryId } : {}),
      },
    }),

  getItem: (itemId: string) =>
    apiClient.get<MenuItem>(`/menu/items/${itemId}`),
};
