import React, { useEffect, useState } from 'react'
import apiClient from '../api/client'

interface MenuItem {
  id: string
  name: string
  base_price: number
  cost_price: number | null
  category_id: string
}

interface InventoryItem {
  id: string
  name: string
  unit: string
  cost_price: number
}

interface Ingredient {
  id: string
  inventory_item_id: string
  quantity: number
  unit: string
}

interface FoodCost {
  menu_item_id: string
  cost_per_serving: number
  selling_price: number
  food_cost_percentage: number
  margin: number
  ingredients: Array<{
    name: string
    quantity: number
    unit: string
    cost: number
  }>
}

export default function RecipeCosting() {
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [selectedItem, setSelectedItem] = useState<string | null>(null)
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [foodCost, setFoodCost] = useState<FoodCost | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddIngredient, setShowAddIngredient] = useState(false)
  const [newIngredient, setNewIngredient] = useState({ inventory_item_id: '', quantity: '', unit: 'g' })

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [menuRes, invRes] = await Promise.all([
        apiClient.get('/menu/items'),
        apiClient.get('/inventory/items'),
      ])
      setMenuItems(menuRes.data)
      setInventoryItems(invRes.data)
    } catch (err) {
      console.error('Failed to load data', err)
    } finally {
      setLoading(false)
    }
  }

  const loadRecipe = async (menuItemId: string) => {
    setSelectedItem(menuItemId)
    try {
      const [recipeRes, costRes] = await Promise.all([
        apiClient.get(`/recipes/${menuItemId}`).catch(() => ({ data: [] })),
        apiClient.get(`/recipes/${menuItemId}/cost`).catch(() => ({ data: null })),
      ])
      setIngredients(Array.isArray(recipeRes.data) ? recipeRes.data : [])
      setFoodCost(costRes.data)
    } catch {
      setIngredients([])
      setFoodCost(null)
    }
  }

  const addIngredient = async () => {
    if (!selectedItem || !newIngredient.inventory_item_id || !newIngredient.quantity) return
    try {
      await apiClient.post('/recipes/ingredients', {
        menu_item_id: selectedItem,
        inventory_item_id: newIngredient.inventory_item_id,
        quantity: parseFloat(newIngredient.quantity),
        unit: newIngredient.unit,
      })
      setShowAddIngredient(false)
      setNewIngredient({ inventory_item_id: '', quantity: '', unit: 'g' })
      loadRecipe(selectedItem)
    } catch (err) {
      console.error('Failed to add ingredient', err)
    }
  }

  const removeIngredient = async (ingredientId: string) => {
    if (!selectedItem) return
    try {
      await apiClient.delete(`/recipes/${selectedItem}/ingredients/${ingredientId}`)
      loadRecipe(selectedItem)
    } catch { /* silent */ }
  }

  const getCostColor = (pct: number) => {
    if (pct <= 30) return 'text-green-600'
    if (pct <= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (loading) return <div className="p-6 text-gray-500">Loading...</div>

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Recipe Costing & Food Cost Analytics</h3>
      </div>

      <div className="flex gap-6">
        {/* Menu Items List */}
        <div className="w-80">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h4 className="font-semibold text-sm">Menu Items</h4>
            </div>
            <div className="max-h-[600px] overflow-auto">
              {menuItems.map(item => {
                // Calculate food cost percentage if cost_price exists
                const costPct = item.cost_price ? (Number(item.cost_price) / Number(item.base_price)) * 100 : null
                return (
                  <div
                    key={item.id}
                    onClick={() => loadRecipe(item.id)}
                    className={`p-3 border-b cursor-pointer hover:bg-gray-50 ${selectedItem === item.id ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-sm">{item.name}</div>
                        <div className="text-xs text-gray-500">₹{Number(item.base_price).toFixed(0)}</div>
                      </div>
                      {costPct !== null && (
                        <span className={`text-xs font-bold ${getCostColor(costPct)}`}>
                          {costPct.toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Recipe Detail */}
        <div className="flex-1">
          {selectedItem ? (
            <div className="space-y-6">
              {/* Food Cost Summary */}
              {foodCost && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h4 className="font-semibold mb-4">
                    {menuItems.find(m => m.id === selectedItem)?.name} - Food Cost
                  </h4>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-500">Cost/Serving</div>
                      <div className="text-2xl font-bold">₹{foodCost.cost_per_serving.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-500">Selling Price</div>
                      <div className="text-2xl font-bold">₹{foodCost.selling_price.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-500">Food Cost %</div>
                      <div className={`text-2xl font-bold ${getCostColor(foodCost.food_cost_percentage)}`}>
                        {foodCost.food_cost_percentage.toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded">
                      <div className="text-sm text-gray-500">Margin</div>
                      <div className="text-2xl font-bold text-green-600">₹{foodCost.margin.toFixed(2)}</div>
                    </div>
                  </div>
                  {/* Food Cost Health */}
                  <div className="mt-4 p-3 rounded-lg text-sm" style={{
                    backgroundColor: foodCost.food_cost_percentage <= 30 ? '#f0fdf4' : foodCost.food_cost_percentage <= 40 ? '#fefce8' : '#fef2f2',
                    color: foodCost.food_cost_percentage <= 30 ? '#166534' : foodCost.food_cost_percentage <= 40 ? '#854d0e' : '#991b1b',
                  }}>
                    {foodCost.food_cost_percentage <= 30 ? '✅ Excellent food cost. Healthy margin.' :
                     foodCost.food_cost_percentage <= 40 ? '⚠️ Acceptable food cost. Monitor closely.' :
                     '🔴 High food cost. Consider adjusting recipe or pricing.'}
                  </div>
                </div>
              )}

              {/* Ingredients */}
              <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b flex justify-between items-center">
                  <h4 className="font-semibold">Recipe Ingredients</h4>
                  <button onClick={() => setShowAddIngredient(true)} className="text-blue-500 text-sm hover:text-blue-700">+ Add Ingredient</button>
                </div>
                {ingredients.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    No ingredients added yet. Add ingredients to calculate food cost.
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ingredient</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Quantity</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Unit</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Cost</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {ingredients.map(ing => {
                        const inv = inventoryItems.find(i => i.id === ing.inventory_item_id)
                        return (
                          <tr key={ing.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">{inv?.name || ing.inventory_item_id}</td>
                            <td className="px-6 py-4 text-right">{ing.quantity}</td>
                            <td className="px-6 py-4 text-right">{ing.unit}</td>
                            <td className="px-6 py-4 text-right">₹{inv ? (Number(inv.cost_price) * ing.quantity / 1000).toFixed(2) : '-'}</td>
                            <td className="px-6 py-4 text-right">
                              <button onClick={() => removeIngredient(ing.id)} className="text-red-500 hover:text-red-700 text-sm">Remove</button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              Select a menu item to view its recipe and food cost
            </div>
          )}
        </div>
      </div>

      {/* Add Ingredient Modal */}
      {showAddIngredient && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Add Ingredient</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ingredient *</label>
                <select value={newIngredient.inventory_item_id} onChange={e => setNewIngredient({...newIngredient, inventory_item_id: e.target.value})} className="w-full px-3 py-2 border rounded">
                  <option value="">Select ingredient...</option>
                  {inventoryItems.map(i => <option key={i.id} value={i.id}>{i.name} ({i.unit}) - ₹{Number(i.cost_price).toFixed(0)}/{i.unit}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label><input type="number" value={newIngredient.quantity} onChange={e => setNewIngredient({...newIngredient, quantity: e.target.value})} className="w-full px-3 py-2 border rounded" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Unit</label><select value={newIngredient.unit} onChange={e => setNewIngredient({...newIngredient, unit: e.target.value})} className="w-full px-3 py-2 border rounded"><option>g</option><option>kg</option><option>ml</option><option>l</option><option>pcs</option></select></div>
              </div>
            </div>
            <div className="flex gap-2 mt-6">
              <button onClick={addIngredient} className="flex-1 bg-blue-500 text-white py-2 rounded hover:bg-blue-600">Add</button>
              <button onClick={() => setShowAddIngredient(false)} className="flex-1 bg-gray-200 text-gray-700 py-2 rounded hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
