import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Orders from './pages/Orders'
import Menu from './pages/Menu'
import Customers from './pages/Customers'
import Reports from './pages/Reports'
import Inventory from './pages/Inventory'
import FloorPlan from './pages/FloorPlan'
import Reservations from './pages/Reservations'
import Loyalty from './pages/Loyalty'
import GSTReports from './pages/GSTReports'
import RecipeCosting from './pages/RecipeCosting'
import Messaging from './pages/Messaging'
import Aggregators from './pages/Aggregators'
import Analytics from './pages/Analytics'
import Security from './pages/Security'
import Franchise from './pages/Franchise'
import KitchenAnalytics from './pages/KitchenAnalytics'
import ReportBuilder from './pages/ReportBuilder'
import AdvancedAnalytics from './pages/AdvancedAnalytics'
import Compliance from './pages/Compliance'
import Settings from './pages/Settings'
import Login from './pages/Login'

function App() {
  const token = localStorage.getItem('admin_token')

  if (!token) {
    return <Login />
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/menu" element={<Menu />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/floor-plan" element={<FloorPlan />} />
          <Route path="/reservations" element={<Reservations />} />
          <Route path="/loyalty" element={<Loyalty />} />
          <Route path="/gst" element={<GSTReports />} />
          <Route path="/recipes" element={<RecipeCosting />} />
          <Route path="/messaging" element={<Messaging />} />
          <Route path="/aggregators" element={<Aggregators />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/security" element={<Security />} />
          <Route path="/franchise" element={<Franchise />} />
          <Route path="/kitchen" element={<KitchenAnalytics />} />
          <Route path="/report-builder" element={<ReportBuilder />} />
          <Route path="/advanced-analytics" element={<AdvancedAnalytics />} />
          <Route path="/compliance" element={<Compliance />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
