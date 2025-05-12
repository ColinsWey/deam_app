import { useState, useEffect } from 'react'
import { ChartBarIcon, ArrowTrendingUpIcon, ShoppingCartIcon, CircleStackIcon } from '@heroicons/react/24/outline'

// Компонент для вывода статистического элемента
const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white rounded-lg shadow p-5">
    <div className="flex items-center">
      <div className={`p-3 rounded-full ${color} text-white mr-4`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-gray-500 text-sm">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  </div>
)

const Dashboard = () => {
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    // Имитация загрузки данных
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)
    
    return () => clearTimeout(timer)
  }, [])
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Панель управления</h1>
      
      {/* Основные показатели */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Создано прогнозов" 
          value="128" 
          icon={ChartBarIcon} 
          color="bg-primary-600" 
        />
        <StatCard 
          title="Точность прогнозов" 
          value="87.5%" 
          icon={ArrowTrendingUpIcon} 
          color="bg-success-600" 
        />
        <StatCard 
          title="Товары в базе" 
          value="1,245" 
          icon={ShoppingCartIcon} 
          color="bg-secondary-600" 
        />
        <StatCard 
          title="Доступно отчетов" 
          value="24" 
          icon={CircleStackIcon} 
          color="bg-warning-600" 
        />
      </div>
      
      {/* Последние логи системы */}
      <div className="bg-white rounded-lg shadow p-5">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Последние системные события</h2>
          <a href="/logs" className="text-primary-600 hover:text-primary-800 text-sm">
            Все логи →
          </a>
        </div>
        
        <div className="border border-gray-200 rounded-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Время
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Сервис
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Сообщение
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {/* Пример логов */}
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  2023-11-25 12:34:56
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  forecast_service
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  Успешно создан прогноз для товара: Электрочайник ID#12345
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  2023-11-25 12:30:21
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  import_service
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  Импортировано 128 новых записей в базу данных
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  2023-11-25 12:15:05
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  auth_service
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  Пользователь admin успешно вошел в систему
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard 