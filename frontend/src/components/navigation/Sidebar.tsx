import { NavLink } from 'react-router-dom'
import { 
  XMarkIcon,
  HomeIcon, 
  DocumentChartBarIcon,
  CloudArrowUpIcon,
  ServerIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

// Типы для компонента
interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

// Навигационные ссылки
const navItems = [
  { name: 'Панель управления', path: '/dashboard', icon: HomeIcon },
  { name: 'Прогнозы', path: '/forecasts', icon: ChartBarIcon },
  { name: 'Отчеты', path: '/reports', icon: DocumentChartBarIcon },
  { name: 'Импорт данных', path: '/import', icon: CloudArrowUpIcon },
  { name: 'Логи системы', path: '/logs', icon: ServerIcon },
]

const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  return (
    <>
      {/* Мобильная версия фона */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Боковая панель */}
      <div className={`
        fixed lg:sticky top-0 left-0 bottom-0 w-64 bg-primary-900 text-white z-50 transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-primary-800">
          <h1 className="text-xl font-bold">DemandForecastApp</h1>
          <button 
            className="p-1 rounded-md lg:hidden hover:bg-primary-800" 
            onClick={onClose}
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        
        <nav className="mt-4 px-2">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) => `
                    flex items-center px-3 py-2 rounded-md 
                    ${isActive ? 'bg-primary-800 text-white' : 'text-primary-100 hover:bg-primary-800'}
                  `}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  <span>{item.name}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  )
}

export default Sidebar 