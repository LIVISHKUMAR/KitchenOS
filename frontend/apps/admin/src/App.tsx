import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import { ErrorBoundary } from './components/ErrorBoundary'
import Layout from './components/Layout'
import Login from './pages/Login'

// Lazy-loaded pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Orders = lazy(() => import('./pages/Orders'))
const Menu = lazy(() => import('./pages/Menu'))
const Customers = lazy(() => import('./pages/Customers'))
const Reports = lazy(() => import('./pages/Reports'))
const Inventory = lazy(() => import('./pages/Inventory'))
const FloorPlan = lazy(() => import('./pages/FloorPlan'))
const Reservations = lazy(() => import('./pages/Reservations'))
const Loyalty = lazy(() => import('./pages/Loyalty'))
const GSTReports = lazy(() => import('./pages/GSTReports'))
const RecipeCosting = lazy(() => import('./pages/RecipeCosting'))
const Messaging = lazy(() => import('./pages/Messaging'))
const Aggregators = lazy(() => import('./pages/Aggregators'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Security = lazy(() => import('./pages/Security'))
const Franchise = lazy(() => import('./pages/Franchise'))
const KitchenAnalytics = lazy(() => import('./pages/KitchenAnalytics'))
const ReportBuilder = lazy(() => import('./pages/ReportBuilder'))
const AdvancedAnalytics = lazy(() => import('./pages/AdvancedAnalytics'))
const Compliance = lazy(() => import('./pages/Compliance'))
const Settings = lazy(() => import('./pages/Settings'))
const Onboarding = lazy(() => import('./pages/Onboarding'))

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
  </div>
)

function App() {
  const token = localStorage.getItem('admin_token')

  if (!token) {
    return <Login />
  }

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Suspense fallback={<PageLoader />}>
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
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </Suspense>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
