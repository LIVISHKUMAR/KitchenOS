import React from 'react';
import { useOfflineSync } from '../hooks/useOfflineSync';

const OfflineIndicator: React.FC = () => {
  const { isOnline, isSyncing, pendingOrders, syncNow } = useOfflineSync();

  if (isOnline && pendingOrders === 0) return null;

  return (
    <div className={`fixed bottom-4 left-4 z-50 flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg text-sm ${
      !isOnline
        ? 'bg-red-500 text-white'
        : pendingOrders > 0
          ? 'bg-yellow-500 text-white'
          : 'bg-green-500 text-white'
    }`}>
      {!isOnline ? (
        <>
          <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
          <span>Offline</span>
          {pendingOrders > 0 && (
            <span className="bg-white/20 px-1.5 py-0.5 rounded text-xs">
              {pendingOrders} queued
            </span>
          )}
        </>
      ) : (
        <>
          {isSyncing ? (
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
          ) : (
            <span className="w-2 h-2 bg-white rounded-full" />
          )}
          <span>{isSyncing ? 'Syncing...' : `${pendingOrders} pending`}</span>
          {!isSyncing && pendingOrders > 0 && (
            <button onClick={syncNow} className="underline hover:no-underline">
              Sync now
            </button>
          )}
        </>
      )}
    </div>
  );
};

export { OfflineIndicator };
