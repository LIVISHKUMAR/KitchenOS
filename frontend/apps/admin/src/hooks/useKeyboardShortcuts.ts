import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface ShortcutMap {
  [key: string]: () => void;
}

export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') {
        if (e.key !== 'Escape') return;
      }

      const parts: string[] = [];
      if (e.ctrlKey || e.metaKey) parts.push('ctrl');
      if (e.shiftKey) parts.push('shift');
      if (e.altKey) parts.push('alt');

      if (e.key.startsWith('F') && e.key.length <= 3) {
        parts.push(e.key.toLowerCase());
      } else {
        parts.push(e.key.toLowerCase());
      }

      const combo = parts.join('+');
      if (shortcuts[combo]) {
        e.preventDefault();
        shortcuts[combo]();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [shortcuts]);
}

export function useAdminShortcuts() {
  const navigate = useNavigate();

  const shortcuts: ShortcutMap = {
    'g+d': () => navigate('/'),
    'g+o': () => navigate('/orders'),
    'g+m': () => navigate('/menu'),
    'g+i': () => navigate('/inventory'),
    'g+r': () => navigate('/reports'),
    'g+c': () => navigate('/customers'),
  };

  useKeyboardShortcuts(shortcuts);
}
