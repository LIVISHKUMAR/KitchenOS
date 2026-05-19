import React, { useEffect, useState } from 'react';
import { tablesApi, type DiningTable } from '../api';

interface TableSelectionProps {
  selectedTable: string | null;
  onTableSelect: (tableId: string | null) => void;
}

const TableSelection: React.FC<TableSelectionProps> = ({ selectedTable, onTableSelect }) => {
  const [tables, setTables] = useState<DiningTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTables();
  }, []);

  const loadTables = async () => {
    try {
      const data = await tablesApi.getTables();
      setTables(data);
    } catch {
      // Tables API not yet available, use fallback
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-gray-500 text-sm">Loading tables...</div>;
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">Tables</h3>
        {selectedTable && (
          <button
            onClick={() => onTableSelect(null)}
            className="text-xs text-blue-500 hover:text-blue-700"
          >
            Clear
          </button>
        )}
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
          </button>
        ))}
      </div>
    </div>
  );
};

export { TableSelection };
