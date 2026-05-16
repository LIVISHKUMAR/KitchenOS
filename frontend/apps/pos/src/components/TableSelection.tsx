import React from 'react';

interface TableSelectionProps {
  selectedTable: string | null;
  onTableSelect: (tableId: string) => void;
}

const TableSelection: React.FC<TableSelectionProps> = ({ selectedTable, onTableSelect }) => {
  // Sample tables - in a real app, this would come from API
  const tables = [
    { id: '1', number: '1', capacity: 4, section: 'Main' },
    { id: '2', number: '2', capacity: 4, section: 'Main' },
    { id: '3', number: '3', capacity: 2, section: 'Terrace' },
    { id: '4', number: '4', capacity: 6, section: 'Private' },
    { id: '5', number: '5', capacity: 4, section: 'Main' },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Select Table</h3>
        {selectedTable && (
          <span className="text-sm text-gray-500">Table #{selectedTable}</span>
        )}
      </div>
      <div className="space-y-2">
        {tables.map(table => (
          <button
            key={table.id}
            onClick={() => onTableSelect(table.id)}
            className={`w-full text-left p-3 border rounded hover:bg-gray-50 
              ${selectedTable === table.id ? 'bg-blue-50 border-blue-500' : 'border-gray-200'}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Table {table.number}</p>
                <p className="text-sm text-gray-500">{table.section} • {table.capacity} seats</p>
              </div>
              <span className="ml-4">
                {selectedTable === table.id ? (
                  <svg className="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                ) : ''}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export { TableSelection };