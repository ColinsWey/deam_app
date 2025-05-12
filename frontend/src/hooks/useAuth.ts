import { useState, useEffect } from 'react'
import { checkAuth, User, logout } from '@services/authService'

interface UseAuthReturn {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  logout: () => void;
}

/**
 * Хук для работы с авторизацией
 * @returns Объект с состоянием авторизации и методами
 */
export const useAuth = (): UseAuthReturn => {
  const [isLoading, setIsLoading] = useState(true)
  const [authState, setAuthState] = useState<{
    isAuthenticated: boolean;
    user: User | null;
  }>({
    isAuthenticated: false,
    user: null
  })
  
  useEffect(() => {
    const checkUserAuth = () => {
      const { isAuthenticated, user } = checkAuth()
      setAuthState({ isAuthenticated, user })
      setIsLoading(false)
    }
    
    checkUserAuth()
  }, [])
  
  const handleLogout = () => {
    logout()
    setAuthState({ isAuthenticated: false, user: null })
  }
  
  return {
    isAuthenticated: authState.isAuthenticated,
    isLoading,
    user: authState.user,
    logout: handleLogout
  }
} 