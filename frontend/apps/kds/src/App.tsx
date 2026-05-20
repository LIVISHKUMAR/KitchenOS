import React from 'react'
import { ErrorBoundary } from './components/ErrorBoundary'
import KDSDashboard from './pages/KDSDashboard'

function App() {
  return (
    <ErrorBoundary>
      <KDSDashboard />
    </ErrorBoundary>
  )
}

export default App
