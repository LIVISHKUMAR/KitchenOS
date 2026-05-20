import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { queryKeys } from '../lib/queryClient';

export function useDashboard() {
  return useQuery({
    queryKey: queryKeys.dashboard.stats(),
    queryFn: () => apiClient.get('/admin/dashboard').then(res => res.data),
    refetchInterval: 30_000,
  });
}
