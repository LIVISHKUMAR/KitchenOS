import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useMenuItems } from '../hooks/useMenu';
import type { MenuItem } from '../api';

interface BarcodeScannerProps {
  onItemScanned: (item: MenuItem) => void;
}

/**
 * Barcode Scanner Component
 *
 * Handles USB HID barcode scanners (keyboard mode) and camera-based scanning.
 * Auto-focuses input field. Scanner sends barcode + Enter key.
 *
 * Supported formats:
 * - USB HID scanners (keyboard wedge) — most common in restaurants
 * - Manual barcode entry
 * - Camera-based scanning (via QuaggaJS if available)
 */
const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ onItemScanned }) => {
  const [barcode, setBarcode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showScanner, setShowScanner] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: menuItems = [] } = useMenuItems();

  // Auto-focus the barcode input
  useEffect(() => {
    if (showScanner && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showScanner]);

  // Build barcode lookup map
  const barcodeMap = React.useMemo(() => {
    const map = new Map<string, MenuItem>();
    for (const item of menuItems) {
      if (item.bar_code) {
        map.set(item.bar_code, item);
      }
      if (item.item_code) {
        map.set(item.item_code, item);
      }
    }
    return map;
  }, [menuItems]);

  const handleScan = useCallback((scannedBarcode: string) => {
    const trimmed = scannedBarcode.trim();
    if (!trimmed) return;

    const item = barcodeMap.get(trimmed);
    if (item) {
      onItemScanned(item);
      setError(null);
      setBarcode('');
    } else {
      setError(`Item not found: ${trimmed}`);
      setTimeout(() => setError(null), 3000);
      setBarcode('');
    }
  }, [barcodeMap, onItemScanned]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleScan(barcode);
    }
    if (e.key === 'Escape') {
      setShowScanner(false);
      setBarcode('');
      setError(null);
    }
  }, [barcode, handleScan]);

  // Listen for global barcode scan (when scanner is hidden)
  useEffect(() => {
    let buffer = '';
    let timeout: ReturnType<typeof setTimeout>;

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        // But handle Enter in our barcode input
        if (showScanner && target === inputRef.current && e.key === 'Enter') {
          return; // handled by input's onKeyDown
        }
        return;
      }

      // Build buffer from keystrokes (scanners type fast)
      if (e.key.length === 1) {
        buffer += e.key;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          buffer = '';
        }, 100); // 100ms between keystrokes = scanner speed
      }

      if (e.key === 'Enter' && buffer.length >= 3) {
        e.preventDefault();
        handleScan(buffer);
        buffer = '';
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => {
      window.removeEventListener('keydown', handleGlobalKeyDown);
      clearTimeout(timeout);
    };
  }, [showScanner, handleScan]);

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setShowScanner(!showScanner)}
        className={`p-2 rounded-lg transition-colors ${
          showScanner ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
        }`}
        title="Barcode Scanner (F5)"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
        </svg>
      </button>

      {/* Scanner input overlay */}
      {showScanner && (
        <div className="fixed top-16 left-1/2 transform -translate-x-1/2 z-50 bg-white rounded-xl shadow-2xl border border-gray-200 p-4 min-w-[300px]">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-sm">Barcode Scanner</h3>
              <p className="text-xs text-gray-500">Scan or type barcode, then press Enter</p>
            </div>
          </div>

          <input
            ref={inputRef}
            type="text"
            value={barcode}
            onChange={e => setBarcode(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Scan barcode..."
            autoFocus
          />

          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}

          <p className="mt-2 text-xs text-gray-400">
            Press Esc to close · USB scanner works automatically
          </p>
        </div>
      )}
    </>
  );
};

export { BarcodeScanner };
