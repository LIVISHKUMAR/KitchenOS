import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { queryKeys } from '../lib/queryClient';

export function useInventoryItems() {
  return useQuery({
    queryKey: queryKeys.inventory.items(),
    queryFn: () => apiClient.get('/inventory/items').then(res => res.data),
  });
}

export function useLowStock() {
  return useQuery({
    queryKey: queryKeys.inventory.lowStock(),
    queryFn: () => apiClient.get('/inventory/low-stock').then(res => res.data),
  });
}
