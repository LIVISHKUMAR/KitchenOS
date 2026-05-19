import React from 'react';

interface NumPadProps {
  onQuantitySelect: (quantity: number) => void;
}

const NumPad: React.FC<NumPadProps> = ({ onQuantitySelect }) => {
  return (
    <div className="grid grid-cols-4 gap-2 p-3 bg-white rounded-lg shadow">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
        <button
          key={num}
          onClick={() => onQuantitySelect(num)}
          className="p-3 text-lg font-semibold bg-gray-100 rounded hover:bg-gray-200 active:bg-gray-300"
        >
          {num}
        </button>
      ))}
      <button
        onClick={() => onQuantitySelect(0)}
        className="p-3 text-lg font-semibold bg-gray-100 rounded hover:bg-gray-200 active:bg-gray-300"
      >
        0
      </button>
      <button
        onClick={() => onQuantitySelect(-1)}
        className="p-3 text-lg font-semibold bg-red-100 text-red-600 rounded hover:bg-red-200 active:bg-red-300"
      >
        C
      </button>
      <button
        onClick={() => onQuantitySelect(-2)}
        className="p-3 text-lg font-semibold bg-blue-100 text-blue-600 rounded hover:bg-blue-200 active:bg-blue-300"
      >
        OK
      </button>
    </div>
  );
};

export { NumPad };
