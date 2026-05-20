import React, { memo } from 'react';
import { LanguageSwitcher } from '../LanguageSwitcher';

interface POSHeaderProps {
  itemCount: number;
  onShiftClosing: () => void;
  onLogout: () => void;
}

const POSHeader: React.FC<POSHeaderProps> = memo(({ itemCount, onShiftClosing, onLogout }) => {
  return (
    <header className="bg-white border-b px-6 py-2 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">POS Terminal</h2>
        <div className="hidden lg:flex items-center gap-1 text-xs text-gray-400">
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px]">F1</kbd><span>Search</span>
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F2</kbd><span>Pay</span>
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F3</kbd><span>Hold</span>
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">F4</kbd><span>Clear</span>
          <kbd className="px-1 py-0.5 bg-gray-100 rounded text-[10px] ml-2">Esc</kbd><span>Close</span>
        </div>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <span className="text-gray-500">{itemCount} item(s)</span>
        <LanguageSwitcher />
        <button onClick={onShiftClosing} className="text-orange-500 hover:text-orange-700 text-sm font-medium">Z-Report</button>
        <button onClick={onLogout} className="text-red-500 hover:text-red-700 text-sm">Logout</button>
      </div>
    </header>
  );
});

POSHeader.displayName = 'POSHeader';
export { POSHeader };
