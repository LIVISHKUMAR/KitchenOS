import React, { useCallback } from 'react';
import { type DiningTable } from '../api';
import { useTables } from '../hooks/useTables';

interface TableSelectionProps {
  selectedTable: string | null;
  onTableSelect: (tableId: string | null) => void;
}

const TableSelection: React.FC<TableSelectionProps> = ({ selectedTable, onTableSelect }) => {
  const { data: tables = [], isLoading, error, refetch } = useTables();

  const handleClick = useCallback((tableId: string) => {
    onTableSelect(selectedTable === tableId ? null : tableId);
  }, [selectedTable, onTableSelect]);

  if (isLoading && tables.length === 0) {
    return (
      <div className="p-4">
        <div className="h-4 bg-gray-200 rounded w-16 mb-3 animate-pulse" />
        <div className="grid grid-cols-3 gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-500 text-sm mb-2">Failed to load tables</div>
        <button onClick={() => refetch()} className="text-xs text-blue-500 hover:text-blue-700">
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
          <button onClick={() => refetch()} className="text-xs text-gray-500 hover:text-gray-700">
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
        {tables.map((table: DiningTable) => (
          <button
            key={table.id}
            onClick={() => handleClick(table.id)}
            className={`p-2 border rounded text-center text-sm transition-all active:scale-95 ${
              selectedTable === table.id
                ? 'bg-blue-500 text-white border-blue-500 shadow-md'
                : table.current_order_id
                  ? 'bg-orange-50 border-orange-300 text-orange-700'
                  : 'bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300'
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
