import { useQuery } from '@tanstack/react-query';
import { tablesApi } from '../api/tables';
import { queryKeys } from '../lib/queryClient';
import { useAuthStore } from '../stores/authStore';

export function useTables() {
  const branchId = useAuthStore(s => s.branchId);

  return useQuery({
    queryKey: queryKeys.tables.list(),
    queryFn: () => tablesApi.getTables(branchId || undefined).then(res => res.data),
    refetchInterval: 15_000, // refresh every 15s for live occupancy
    enabled: !!branchId,
  });
}
