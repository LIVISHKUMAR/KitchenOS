import React from 'react';

interface MenuGridProps {
  onItemSelect: (menuItem: any) => void;
}

const MenuGrid: React.FC<MenuGridProps> = ({ onItemSelect }) => {
  // Sample menu items - in a real app, this would come from API
  const menuItems = [
    {
      id: '1',
      name: 'Margherita Pizza',
      description: 'Classic pizza with tomato sauce and mozzarella',
      base_price: 12.99,
      item_code: 'PIZ001',
      is_veg: true,
    },
    {
      id: '2',
      name: 'Chicken Burger',
      description: 'Grilled chicken burger with lettuce and mayo',
      base_price: 9.99,
      item_code: 'BUR001',
      is_veg: false,
    },
    {
      id: '3',
      name: 'Caesar Salad',
      description: 'Fresh romaine lettuce with caesar dressing',
      base_price: 7.99,
      item_code: 'SAL001',
      is_veg: true,
    },
    {
      id: '4',
      name: 'Chocolate Cake',
      description: 'Rich chocolate cake with vanilla ice cream',
      base_price: 5.99,
      item_code: 'DSS001',
      is_veg: true,
    },
    {
      id: '5',
      name: 'Coca Cola',
      description: 'Refreshing cold drink',
      base_price: 2.99,
      item_code: 'DRK001',
      is_veg: true,
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {menuItems.map(item => (
        <div 
          key={item.id} 
          onClick={() => onItemSelect(item)}
          className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer p-4"
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded flex items-center justify-center">
              {(item.is_veg ? '🥗' : '🍖')}
            </div>
            <div className="ml-3">
              <h3 className="font-semibold">{item.name}</h3>
              <p className="text-sm text-gray-500">{item.description}</p>
              <p className="mt-2 font-bold text-lg">₹{item.base_price}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export { MenuGrid };