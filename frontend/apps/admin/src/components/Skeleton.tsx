import React from 'react';

export const StatCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-xl border border-gray-100 p-5">
    <div className="flex items-center justify-between">
      <div>
        <div className="h-3 bg-gray-200 rounded w-20 mb-2 animate-pulse" />
        <div className="h-8 bg-gray-200 rounded w-24 animate-pulse" />
      </div>
      <div className="w-12 h-12 bg-gray-200 rounded-xl animate-pulse" />
    </div>
  </div>
);

export const TableRowSkeleton: React.FC<{ columns?: number }> = ({ columns = 4 }) => (
  <tr>
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="px-6 py-4">
        <div className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: i === 0 ? '80%' : '60%' }} />
      </td>
    ))}
  </tr>
);
