import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { queryKeys } from '../lib/queryClient';

export function useOrders(statusFilter?: string) {
  return useQuery({
    queryKey: queryKeys.orders.list({ status: statusFilter || 'all' }),
    queryFn: () => {
      const params: Record<string, string> = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;
      return apiClient.get('/orders/', { params }).then(res => res.data);
    },
    refetchInterval: 15_000,
  });
}
