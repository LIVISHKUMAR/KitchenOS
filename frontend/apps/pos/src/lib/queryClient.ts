import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30 seconds - data considered fresh
      gcTime: 5 * 60_000, // 5 minutes - garbage collection time
      retry: 2, // retry failed requests twice
      refetchOnWindowFocus: false, // don't refetch on window focus for POS
      refetchOnReconnect: true, // refetch when coming back online
    },
    mutations: {
      retry: 1, // retry failed mutations once
    },
  },
});

// Query keys for consistent caching
export const queryKeys = {
  menu: {
    all: ['menu'] as const,
    items: () => [...queryKeys.menu.all, 'items'] as const,
    categories: () => [...queryKeys.menu.all, 'categories'] as const,
  },
  tables: {
    all: ['tables'] as const,
    list: () => [...queryKeys.tables.all, 'list'] as const,
  },
  orders: {
    all: ['orders'] as const,
    active: () => [...queryKeys.orders.all, 'active'] as const,
    detail: (id: string) => [...queryKeys.orders.all, id] as const,
  },
  customers: {
    all: ['customers'] as const,
    search: (query: string) => [...queryKeys.customers.all, 'search', query] as const,
    byPhone: (phone: string) => [...queryKeys.customers.all, 'phone', phone] as const,
  },
  payments: {
    all: ['payments'] as const,
    byOrder: (orderId: string) => [...queryKeys.payments.all, 'order', orderId] as const,
  },
  kot: {
    all: ['kot'] as const,
    active: () => [...queryKeys.kot.all, 'active'] as const,
    summary: () => [...queryKeys.kot.all, 'summary'] as const,
  },
  printers: {
    all: ['printers'] as const,
    list: () => [...queryKeys.printers.all, 'list'] as const,
  },
} as const;
