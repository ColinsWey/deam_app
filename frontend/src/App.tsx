import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'

// Layouts
import MainLayout from '@components/layouts/MainLayout'

// Pages (ленивая загрузка)
const Dashboard = lazy(() => import('@pages/Dashboard'))
const LogsViewer = lazy(() => import('@pages/LogsViewer'))
const NotFound = lazy(() => import('@pages/NotFound'))
const Login = lazy(() => import('@pages/Login'))

// Компонент загрузки
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
  </div>
)

const App = () => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Публичные маршруты */}
        <Route path="/login" element={<Login />} />
        
        {/* Защищенные маршруты */}
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="logs" element={<LogsViewer />} />
        </Route>
        
        {/* Маршрут 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}

export default App 