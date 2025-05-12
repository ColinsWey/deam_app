import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bars3Icon, BellIcon, UserCircleIcon } from '@heroicons/react/24/outline'

interface HeaderProps {
  onMenuClick: () => void;
}

const Header = ({ onMenuClick }: HeaderProps) => {
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  
  const handleLogout = () => {
    // Здесь будет логика выхода, очистка токена и т.д.
    console.log('Выход из системы')
    navigate('/login')
  }
  
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between h-16 px-4">
        {/* Кнопка меню для мобильных устройств */}
        <button
          className="p-1 rounded-md text-gray-500 lg:hidden hover:bg-gray-100"
          onClick={onMenuClick}
        >
          <Bars3Icon className="w-6 h-6" />
        </button>
        
        {/* Заголовок страницы - скрыт на мобильных */}
        <h1 className="text-xl font-semibold text-gray-800 hidden md:block">
          Панель управления
        </h1>
        
        {/* Правая часть хедера */}
        <div className="flex items-center space-x-2">
          {/* Уведомления */}
          <button className="p-1 rounded-md text-gray-500 hover:bg-gray-100 relative">
            <BellIcon className="w-6 h-6" />
            <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-red-500"></span>
          </button>
          
          {/* Профиль пользователя */}
          <div className="relative">
            <button
              className="flex items-center text-gray-600 hover:text-gray-900"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <UserCircleIcon className="w-8 h-8 text-gray-500" />
              <span className="ml-2 hidden md:block">Администратор</span>
            </button>
            
            {/* Выпадающее меню профиля */}
            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-gray-200">
                <button
                  className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100"
                  onClick={handleLogout}
                >
                  Выйти
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header 