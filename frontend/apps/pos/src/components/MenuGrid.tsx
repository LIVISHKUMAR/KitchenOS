import React, { useState, useMemo } from 'react';
import { type MenuItem, type MenuCategory } from '../api';
import { useMenuItems, useMenuCategories } from '../hooks/useMenu';

interface MenuGridProps {
  onItemSelect: (menuItem: MenuItem) => void;
}

// Skeleton loader component
const MenuSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
        <div className="flex items-start">
          <div className="h-10 w-10 bg-gray-200 rounded" />
          <div className="ml-3 flex-1 space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-3 bg-gray-100 rounded w-1/2" />
            <div className="h-5 bg-gray-200 rounded w-1/3" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

const MenuGrid: React.FC<MenuGridProps> = ({ onItemSelect }) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const { data: allItems = [], isLoading: itemsLoading, error: itemsError, refetch: refetchItems } = useMenuItems();
  const { data: allCategories = [], isLoading: catsLoading } = useMenuCategories();

  // Memoize filtered data
  const items = useMemo(() => allItems.filter((i: MenuItem) => i.is_available), [allItems]);
  const categories = useMemo(() => allCategories.filter((c: MenuCategory) => c.is_active), [allCategories]);

  const filteredItems = useMemo(() => items.filter(item => {
    const matchesCategory = !selectedCategory || item.category_id === selectedCategory;
    const matchesSearch = !search || item.name.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  }), [items, selectedCategory, search]);

  const loading = itemsLoading || catsLoading;

  if (loading) {
    return (
      <div>
        <div className="mb-4">
          <div className="h-10 bg-gray-200 rounded-lg animate-pulse" />
        </div>
        <div className="flex gap-2 mb-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-8 w-20 bg-gray-200 rounded-full animate-pulse" />
          ))}
        </div>
        <MenuSkeleton />
      </div>
    );
  }

  if (itemsError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-red-500">Failed to load menu</p>
        <button onClick={() => refetchItems()} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search menu... (F1)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-search-input
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Category tabs */}
      {categories.length > 0 && (
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
              !selectedCategory ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 rounded-full text-sm whitespace-nowrap transition-colors ${
                selectedCategory === cat.id ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      )}

      {/* Menu grid */}
      {filteredItems.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          {items.length === 0 ? 'No menu items available.' : 'No items match your search.'}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map(item => (
            <div
              key={item.id}
              onClick={() => onItemSelect(item)}
              className="bg-white rounded-lg shadow hover:shadow-md transition-all cursor-pointer p-4 active:scale-95"
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded flex items-center justify-center text-lg">
                  {item.is_veg ? '🟢' : '🔴'}
                </div>
                <div className="ml-3 flex-1 min-w-0">
                  <h3 className="font-semibold truncate">{item.name}</h3>
                  {item.description && (
                    <p className="text-sm text-gray-500 line-clamp-2">{item.description}</p>
                  )}
                  <div className="mt-2 flex items-center justify-between">
                    <span className="font-bold text-lg">₹{Number(item.base_price).toFixed(2)}</span>
                    {item.item_code && (
                      <span className="text-xs text-gray-400">{item.item_code}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export { MenuGrid };
