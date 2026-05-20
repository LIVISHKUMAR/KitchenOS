/**
 * Offline sync engine.
 * Queues orders when offline, syncs when connection is restored.
 */

import { offlineDB, type OfflineOrder } from './db';
import apiClient from '../api/client';

type SyncStatus = 'idle' | 'syncing' | 'error';
type ConnectionStatus = 'online' | 'offline';

type StatusCallback = (status: { sync: SyncStatus; connection: ConnectionStatus; pendingCount: number }) => void;

class SyncEngine {
  private listeners: Set<StatusCallback> = new Set();
  private syncInterval: ReturnType<typeof setInterval> | null = null;
  private _connectionStatus: ConnectionStatus = navigator.onLine ? 'online' : 'offline';
  private _syncStatus: SyncStatus = 'idle';

  get connectionStatus() {
    return this._connectionStatus;
  }

  get syncStatus() {
    return this._syncStatus;
  }

  start() {
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);

    // Periodic sync attempt every 30 seconds
    this.syncInterval = setInterval(() => {
      if (this._connectionStatus === 'online') {
        this.syncQueuedOrders();
      }
    }, 30000);

    // Initial sync attempt
    if (this._connectionStatus === 'online') {
      this.syncQueuedOrders();
    }
  }

  stop() {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  subscribe(callback: StatusCallback) {
    this.listeners.add(callback);
    // Immediately notify with current status
    this.notify();
    return () => this.listeners.delete(callback);
  }

  private notify() {
    offlineDB.getQueuedOrders().then(orders => {
      const status = {
        sync: this._syncStatus,
        connection: this._connectionStatus,
        pendingCount: orders.length,
      };
      this.listeners.forEach(cb => cb(status));
    });
  }

  private handleOnline = () => {
    this._connectionStatus = 'online';
    this.notify();
    this.syncQueuedOrders();
  };

  private handleOffline = () => {
    this._connectionStatus = 'offline';
    this.notify();
  };

  /**
   * Queue an order for offline sync.
   * Returns the offline order ID.
   */
  async queueOrder(orderData: Record<string, unknown>): Promise<string> {
    const id = `offline-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const offlineOrder: OfflineOrder = {
      id,
      data: orderData,
      endpoint: '/api/v1/orders/',
      method: 'POST',
      created_at: Date.now(),
      synced: false,
      retries: 0,
    };
    await offlineDB.queueOrder(offlineOrder);
    this.notify();
    return id;
  }

  /**
   * Sync all queued orders to the server.
   */
  async syncQueuedOrders(): Promise<void> {
    if (this._syncStatus === 'syncing') return;

    const queued = await offlineDB.getQueuedOrders();
    if (queued.length === 0) return;

    this._syncStatus = 'syncing';
    this.notify();

    let successCount = 0;
    let failCount = 0;

    for (const order of queued) {
      try {
        await apiClient.post(order.endpoint, order.data);
        await offlineDB.markOrderSynced(order.id);
        successCount++;
      } catch (err) {
        await offlineDB.incrementRetry(order.id);
        failCount++;
        // Stop retrying after 5 attempts
        if (order.retries >= 5) {
          await offlineDB.markOrderSynced(order.id); // Mark as synced to remove from queue
        }
      }
    }

    this._syncStatus = failCount > 0 ? 'error' : 'idle';
    this.notify();

    if (successCount > 0) {
      console.log(`Synced ${successCount} offline orders`);
    }
  }

  /**
   * Get count of pending orders.
   */
  async getPendingCount(): Promise<number> {
    const orders = await offlineDB.getQueuedOrders();
    return orders.length;
  }
}

export const syncEngine = new SyncEngine();
