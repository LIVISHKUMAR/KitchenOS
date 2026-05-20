import React, { useEffect } from 'react'
import { useAuthStore } from './stores/authStore'
import { ToastProvider } from './components/Toast'
import { ErrorBoundary } from './components/ErrorBoundary'
import { OfflineIndicator } from './components/OfflineIndicator'
import LoginPage from './pages/LoginPage'
import POSPage from './pages/POSPage'

const App = () => {
  const { isAuthenticated, checkAuth } = useAuthStore()

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return (
    <ErrorBoundary>
      <ToastProvider>
        {!isAuthenticated ? <LoginPage /> : <POSPage />}
        <OfflineIndicator />
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
