import React, { useEffect } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from './stores/authStore'
import { queryClient } from './lib/queryClient'
import { ToastProvider } from './components/Toast'
import { ErrorBoundary } from './components/ErrorBoundary'
import { OfflineIndicator } from './components/OfflineIndicator'
import LoginPage from './pages/LoginPage'
import POSPage from './pages/POSPage'

const AppContent = () => {
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  if (!isAuthenticated) return <LoginPage />
  return <POSPage />
}

const App = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AppContent />
          <OfflineIndicator />
        </ToastProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
