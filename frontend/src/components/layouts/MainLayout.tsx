import { Outlet } from 'react-router-dom'
import Sidebar from '@components/navigation/Sidebar'
import Header from '@components/navigation/Header'
import { useState } from 'react'

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Боковая панель */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      {/* Основной контент */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
        
        <footer className="bg-white border-t border-gray-200 py-3 px-6 text-center text-gray-500 text-sm">
          DemandForecastApp &copy; {new Date().getFullYear()}
        </footer>
      </div>
    </div>
  )
}

export default MainLayout 