import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

export const queryKeys = {
  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
  },
  orders: {
    all: ['orders'] as const,
    list: (filters?: Record<string, string>) => [...queryKeys.orders.all, 'list', filters] as const,
    detail: (id: string) => [...queryKeys.orders.all, id] as const,
  },
  menu: {
    all: ['menu'] as const,
    items: () => [...queryKeys.menu.all, 'items'] as const,
    categories: () => [...queryKeys.menu.all, 'categories'] as const,
  },
  customers: {
    all: ['customers'] as const,
    list: () => [...queryKeys.customers.all, 'list'] as const,
  },
  inventory: {
    all: ['inventory'] as const,
    items: () => [...queryKeys.inventory.all, 'items'] as const,
    lowStock: () => [...queryKeys.inventory.all, 'low-stock'] as const,
  },
  reports: {
    all: ['reports'] as const,
    dailySales: (date?: string) => [...queryKeys.reports.all, 'daily-sales', date] as const,
    itemSales: () => [...queryKeys.reports.all, 'item-sales'] as const,
    hourlySales: (date?: string) => [...queryKeys.reports.all, 'hourly-sales', date] as const,
  },
  tables: {
    all: ['tables'] as const,
    list: () => [...queryKeys.tables.all, 'list'] as const,
  },
  reservations: {
    all: ['reservations'] as const,
    list: (date?: string) => [...queryKeys.reservations.all, 'list', date] as const,
    waitlist: () => [...queryKeys.reservations.all, 'waitlist'] as const,
  },
  loyalty: {
    all: ['loyalty'] as const,
    history: (customerId: string) => [...queryKeys.loyalty.all, 'history', customerId] as const,
  },
  audit: {
    all: ['audit'] as const,
    logs: () => [...queryKeys.audit.all, 'logs'] as const,
  },
} as const;
