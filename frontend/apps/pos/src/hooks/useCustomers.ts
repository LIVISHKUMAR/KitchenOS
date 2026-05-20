import { useQuery } from '@tanstack/react-query';
import { customersApi } from '../api/customers';
import { queryKeys } from '../lib/queryClient';

export function useCustomerByPhone(phone: string) {
  return useQuery({
    queryKey: queryKeys.customers.byPhone(phone),
    queryFn: () => customersApi.getByPhone(phone).then(res => res.data),
    enabled: phone.length >= 3,
    staleTime: 30_000,
  });
}
