/**
 * Hook for offline sync functionality.
 * Registers service worker and exposes sync status.
 */

import { useState, useEffect } from 'react';
import { syncEngine } from '../offline/sync';

interface OfflineStatus {
  isOnline: boolean;
  isSyncing: boolean;
  pendingOrders: number;
}

export function useOfflineSync(): OfflineStatus & { syncNow: () => Promise<void> } {
  const [status, setStatus] = useState<OfflineStatus>({
    isOnline: navigator.onLine,
    isSyncing: false,
    pendingOrders: 0,
  });

  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.warn('Service worker registration failed:', err);
      });
    }

    // Start sync engine
    syncEngine.start();

    // Subscribe to status changes
    const unsubscribe = syncEngine.subscribe(({ sync, connection, pendingCount }) => {
      setStatus({
        isOnline: connection === 'online',
        isSyncing: sync === 'syncing',
        pendingOrders: pendingCount,
      });
    });

    return () => {
      unsubscribe();
      syncEngine.stop();
    };
  }, []);

  const syncNow = async () => {
    await syncEngine.syncQueuedOrders();
  };

  return { ...status, syncNow };
}
