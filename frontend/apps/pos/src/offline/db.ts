/**
 * IndexedDB wrapper for offline data storage.
 * Stores menu, tables, and queued orders locally.
 */

const DB_NAME = 'kitchenos-pos';
const DB_VERSION = 1;

interface OfflineOrder {
  id: string;
  data: Record<string, unknown>;
  endpoint: string;
  method: string;
  created_at: number;
  synced: boolean;
  retries: number;
}

class OfflineDB {
  private db: IDBDatabase | null = null;

  async open(): Promise<IDBDatabase> {
    if (this.db) return this.db;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains('menu')) {
          db.createObjectStore('menu', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('categories')) {
          db.createObjectStore('categories', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('tables')) {
          db.createObjectStore('tables', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('orders')) {
          const ordersStore = db.createObjectStore('orders', { keyPath: 'id' });
          ordersStore.createIndex('synced', 'synced', { unique: false });
        }
        if (!db.objectStoreNames.contains('meta')) {
          db.createObjectStore('meta', { keyPath: 'key' });
        }
      };

      request.onsuccess = (event) => {
        this.db = (event.target as IDBOpenDBRequest).result;
        resolve(this.db);
      };

      request.onerror = () => reject(request.error);
    });
  }

  async put(storeName: string, data: unknown): Promise<void> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      store.put(data);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async get<T>(storeName: string, key: string): Promise<T | undefined> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.get(key);
      request.onsuccess = () => resolve(request.result as T);
      request.onerror = () => reject(request.error);
    });
  }

  async getAll<T>(storeName: string): Promise<T[]> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readonly');
      const store = tx.objectStore(storeName);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result as T[]);
      request.onerror = () => reject(request.error);
    });
  }

  async delete(storeName: string, key: string): Promise<void> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      store.delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async clear(storeName: string): Promise<void> {
    const db = await this.open();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, 'readwrite');
      const store = tx.objectStore(storeName);
      store.clear();
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  // Menu caching
  async cacheMenu(items: unknown[], categories: unknown[]): Promise<void> {
    for (const item of items) await this.put('menu', item);
    for (const cat of categories) await this.put('categories', cat);
  }

  async getCachedMenu(): Promise<{ items: unknown[]; categories: unknown[] }> {
    const items = await this.getAll('menu');
    const categories = await this.getAll('categories');
    return { items, categories };
  }

  // Table caching
  async cacheTables(tables: unknown[]): Promise<void> {
    await this.clear('tables');
    for (const table of tables) await this.put('tables', table);
  }

  async getCachedTables(): Promise<unknown[]> {
    return this.getAll('tables');
  }

  // Offline order queue
  async queueOrder(order: OfflineOrder): Promise<void> {
    await this.put('orders', { ...order, synced: false, retries: 0 });
  }

  async getQueuedOrders(): Promise<OfflineOrder[]> {
    const all = await this.getAll<OfflineOrder>('orders');
    return all.filter(o => !o.synced);
  }

  async markOrderSynced(orderId: string): Promise<void> {
    const order = await this.get<OfflineOrder>('orders', orderId);
    if (order) {
      await this.put('orders', { ...order, synced: true });
    }
  }

  async incrementRetry(orderId: string): Promise<void> {
    const order = await this.get<OfflineOrder>('orders', orderId);
    if (order) {
      await this.put('orders', { ...order, retries: order.retries + 1 });
    }
  }

  // Metadata
  async setMeta(key: string, value: unknown): Promise<void> {
    await this.put('meta', { key, value });
  }

  async getMeta<T>(key: string): Promise<T | undefined> {
    const meta = await this.get<{ key: string; value: T }>('meta', key);
    return meta?.value;
  }
}

export const offlineDB = new OfflineDB();
export type { OfflineOrder };
