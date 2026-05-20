import React, { useEffect, useState, useCallback } from 'react';
import { tablesApi, type DiningTable } from '../api';
import { useAuthStore } from '../stores/authStore';

interface TableSelectionProps {
  selectedTable: string | null;
  onTableSelect: (tableId: string | null) => void;
}

const TableSelection: React.FC<TableSelectionProps> = ({ selectedTable, onTableSelect }) => {
  const [tables, setTables] = useState<DiningTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const branchId = useAuthStore(s => s.branchId);

  const loadTables = useCallback(async () => {
    if (!branchId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await tablesApi.getTables(branchId);
      setTables(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  }, [branchId]);

  useEffect(() => {
    loadTables();
  }, [loadTables]);

  // Refresh tables every 30 seconds for live occupancy
  useEffect(() => {
    const interval = setInterval(loadTables, 30000);
    return () => clearInterval(interval);
  }, [loadTables]);

  if (loading && tables.length === 0) {
    return <div className="p-4 text-gray-500 text-sm">Loading tables...</div>;
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-500 text-sm mb-2">{error}</div>
        <button onClick={loadTables} className="text-xs text-blue-500 hover:text-blue-700">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">Tables</h3>
        <div className="flex gap-2">
          <button onClick={loadTables} className="text-xs text-gray-500 hover:text-gray-700">
            Refresh
          </button>
          {selectedTable && (
            <button
              onClick={() => onTableSelect(null)}
              className="text-xs text-blue-500 hover:text-blue-700"
            >
              Clear
            </button>
          )}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {tables.map(table => (
          <button
            key={table.id}
            onClick={() => onTableSelect(selectedTable === table.id ? null : table.id)}
            className={`p-2 border rounded text-center text-sm transition-colors ${
              selectedTable === table.id
                ? 'bg-blue-500 text-white border-blue-500'
                : table.current_order_id
                  ? 'bg-orange-50 border-orange-300 text-orange-700'
                  : 'bg-white border-gray-200 hover:bg-gray-50'
            }`}
          >
            <div className="font-medium">{table.table_number}</div>
            <div className="text-xs opacity-75">{table.capacity}p</div>
            {table.section && <div className="text-xs opacity-50">{table.section}</div>}
          </button>
        ))}
      </div>
    </div>
  );
};

export { TableSelection };
