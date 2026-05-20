import apiClient from './client';

export interface DiningTable {
  id: string;
  table_number: string;
  capacity: number;
  section: string | null;
  is_active: boolean;
  current_order_id: string | null;
}

export const tablesApi = {
  getTables: async (branchId?: string): Promise<DiningTable[]> => {
    const params: Record<string, string> = {};
    if (branchId) params.branch_id = branchId;
    const { data } = await apiClient.get('/tables/', { params });
    return data;
  },

  getAvailableTables: async (branchId: string): Promise<DiningTable[]> => {
    const { data } = await apiClient.get('/tables/available', { params: { branch_id: branchId } });
    return data;
  },
};
