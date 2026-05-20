import React, { useState } from 'react'
import apiClient from '../api/client'
import { useNavigate } from 'react-router-dom'

interface Step {
  id: string
  title: string
  description: string
  icon: string
}

const STEPS: Step[] = [
  { id: 'welcome', title: 'Welcome', description: 'Your restaurant setup begins here', icon: '🎉' },
  { id: 'restaurant', title: 'Restaurant Info', description: 'Basic details about your restaurant', icon: '🏪' },
  { id: 'menu', title: 'Add Menu Items', description: 'Add your first menu items', icon: '🍽️' },
  { id: 'tables', title: 'Setup Tables', description: 'Configure your dining area', icon: '🪑' },
  { id: 'complete', title: 'All Set!', description: 'Your restaurant is ready', icon: '✅' },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)

  // Restaurant info
  const [restaurantName, setRestaurantName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [businessType, setBusinessType] = useState('restaurant')

  // Menu items
  const [menuItems, setMenuItems] = useState([
    { name: '', price: '', category: 'Main Course' },
  ])

  // Tables
  const [tableCount, setTableCount] = useState(5)

  const step = STEPS[currentStep]

  const handleNext = async () => {
    if (currentStep === 1) {
      // Save restaurant info
      setLoading(true)
      try {
        await apiClient.put('/tenants/me', { name: restaurantName, phone })
        await apiClient.put('/branches/me', { address, business_type: businessType })
      } catch (err) {
        console.error('Failed to save', err)
      } finally {
        setLoading(false)
      }
    }

    if (currentStep === 2) {
      // Save menu items
      setLoading(true)
      try {
        const categoryRes = await apiClient.post('/menu/categories', { name: 'Main Course' })
        const categoryId = categoryRes.data.id
        for (const item of menuItems) {
          if (item.name && item.price) {
            await apiClient.post('/menu/items', {
              name: item.name,
              base_price: parseFloat(item.price),
              category_id: categoryId,
              is_veg: true,
              is_available: true,
            })
          }
        }
      } catch (err) {
        console.error('Failed to save menu', err)
      } finally {
        setLoading(false)
      }
    }

    if (currentStep === 3) {
      // Create tables
      setLoading(true)
      try {
        for (let i = 1; i <= tableCount; i++) {
          await apiClient.post('/tables/', {
            table_number: `T${i}`,
            capacity: i <= 2 ? 2 : i <= 5 ? 4 : 6,
            section: 'Main Hall',
          })
        }
      } catch (err) {
        console.error('Failed to create tables', err)
      } finally {
        setLoading(false)
      }
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1)
  }

  const handleFinish = () => {
    localStorage.setItem('onboarding_complete', 'true')
    navigate('/')
  }

  const addMenuItem = () => {
    setMenuItems([...menuItems, { name: '', price: '', category: 'Main Course' }])
  }

  const updateMenuItem = (index: number, field: string, value: string) => {
    const updated = [...menuItems]
    updated[index] = { ...updated[index], [field]: value }
    setMenuItems(updated)
  }

  const removeMenuItem = (index: number) => {
    setMenuItems(menuItems.filter((_, i) => i !== index))
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress */}
        <div className="flex items-center justify-between mb-8">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${
                i < currentStep ? 'bg-green-500 text-white' :
                i === currentStep ? 'bg-blue-500 text-white' :
                'bg-gray-200 text-gray-500'
              }`}>
                {i < currentStep ? '✓' : i + 1}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-12 h-1 mx-1 ${i < currentStep ? 'bg-green-500' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="text-center mb-6">
            <span className="text-4xl">{step.icon}</span>
            <h2 className="text-2xl font-bold text-gray-900 mt-3">{step.title}</h2>
            <p className="text-gray-500 mt-1">{step.description}</p>
          </div>

          {/* Step Content */}
          {currentStep === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">
                Welcome to KitchenOS! Let's set up your restaurant in just a few steps.
              </p>
              <p className="text-sm text-gray-500">
                This will take about 3 minutes. You can always change these settings later.
              </p>
            </div>
          )}

          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Restaurant Name *</label>
                <input
                  type="text"
                  value={restaurantName}
                  onChange={e => setRestaurantName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g. Spice Garden"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="+91 98765 43210"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <textarea
                  value={address}
                  onChange={e => setAddress(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="123 Main Street, City"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Business Type</label>
                <select
                  value={businessType}
                  onChange={e => setBusinessType(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="restaurant">Restaurant</option>
                  <option value="cloud_kitchen">Cloud Kitchen</option>
                  <option value="cafe">Cafe</option>
                  <option value="bar">Bar & Lounge</option>
                  <option value="food_truck">Food Truck</option>
                </select>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500 mb-4">Add a few menu items to get started. You can add more later.</p>
              {menuItems.map((item, i) => (
                <div key={i} className="flex gap-3 items-end">
                  <div className="flex-1">
                    <label className="block text-xs text-gray-500 mb-1">Item Name</label>
                    <input
                      type="text"
                      value={item.name}
                      onChange={e => updateMenuItem(i, 'name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="e.g. Butter Chicken"
                    />
                  </div>
                  <div className="w-32">
                    <label className="block text-xs text-gray-500 mb-1">Price (₹)</label>
                    <input
                      type="number"
                      value={item.price}
                      onChange={e => updateMenuItem(i, 'price', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="350"
                    />
                  </div>
                  {menuItems.length > 1 && (
                    <button onClick={() => removeMenuItem(i)} className="px-3 py-2 text-red-500 hover:text-red-700 text-sm">
                      ✕
                    </button>
                  )}
                </div>
              ))}
              <button onClick={addMenuItem} className="text-blue-500 hover:text-blue-700 text-sm font-medium">
                + Add another item
              </button>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500 mb-4">How many tables does your restaurant have?</p>
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={() => setTableCount(Math.max(1, tableCount - 1))}
                  className="w-12 h-12 bg-gray-100 rounded-lg text-xl font-bold hover:bg-gray-200"
                >
                  -
                </button>
                <span className="text-4xl font-bold text-gray-900 w-16 text-center">{tableCount}</span>
                <button
                  onClick={() => setTableCount(Math.min(50, tableCount + 1))}
                  className="w-12 h-12 bg-gray-100 rounded-lg text-xl font-bold hover:bg-gray-200"
                >
                  +
                </button>
              </div>
              <p className="text-center text-sm text-gray-500">
                Tables will be numbered T1 to T{tableCount}
              </p>
            </div>
          )}

          {currentStep === 4 && (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🎉</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">Your restaurant is ready!</h3>
              <p className="text-gray-500 mb-6">
                You've set up {restaurantName || 'your restaurant'} with {menuItems.filter(i => i.name).length} menu items and {tableCount} tables.
              </p>
              <p className="text-sm text-gray-400">
                You can always add more items, configure printers, and customize settings from the admin panel.
              </p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>
            {currentStep < STEPS.length - 1 ? (
              <button
                onClick={handleNext}
                disabled={loading || (currentStep === 1 && !restaurantName)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {loading ? 'Saving...' : 'Continue'}
              </button>
            ) : (
              <button
                onClick={handleFinish}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              >
                Go to Dashboard
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
