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
  // Dining tables don't have a dedicated endpoint yet,
  // so we use branches endpoint and derive tables from the branch.
  // For now, return mock data until a /tables endpoint is added.
  getTables: async (_branchId?: string): Promise<DiningTable[]> => {
    // TODO: Replace with real API call once /api/v1/tables endpoint exists
    return [
      { id: '1', table_number: 'T1', capacity: 4, section: 'Main', is_active: true, current_order_id: null },
      { id: '2', table_number: 'T2', capacity: 4, section: 'Main', is_active: true, current_order_id: null },
      { id: '3', table_number: 'T3', capacity: 2, section: 'Terrace', is_active: true, current_order_id: null },
      { id: '4', table_number: 'T4', capacity: 6, section: 'Private', is_active: true, current_order_id: null },
      { id: '5', table_number: 'T5', capacity: 4, section: 'Main', is_active: true, current_order_id: null },
    ];
  },
};
