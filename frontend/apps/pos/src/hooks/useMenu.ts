import { useQuery } from '@tanstack/react-query';
import { menuApi } from '../api/menu';
import { queryKeys } from '../lib/queryClient';

export function useMenuItems() {
  return useQuery({
    queryKey: queryKeys.menu.items(),
    queryFn: () => menuApi.getItems().then(res => res.data),
    staleTime: 60_000, // menu items rarely change during service
  });
}

export function useMenuCategories() {
  return useQuery({
    queryKey: queryKeys.menu.categories(),
    queryFn: () => menuApi.getCategories().then(res => res.data),
    staleTime: 60_000,
  });
}
