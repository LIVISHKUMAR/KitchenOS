import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/client';
import { queryKeys } from '../lib/queryClient';

export function useActiveKOT() {
  return useQuery({
    queryKey: queryKeys.kot.active(),
    queryFn: () => apiClient.get('/kot/').then(res => res.data),
    refetchInterval: 10_000,
  });
}

export function useKOTSummary() {
  return useQuery({
    queryKey: queryKeys.kot.summary(),
    queryFn: () => apiClient.get('/kot/summary').then(res => res.data),
    refetchInterval: 10_000,
  });
}
