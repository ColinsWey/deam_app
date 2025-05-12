import axios from 'axios'
import { jwtDecode } from 'jwt-decode'

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface DecodedToken {
  sub: string;
  username: string;
  email: string;
  role: string;
  exp: number;
}

/**
 * Авторизация пользователя
 * @param username Имя пользователя
 * @param password Пароль
 * @returns Promise с ответом авторизации
 */
export const login = async (username: string, password: string): Promise<User> => {
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  
  try {
    const response = await axios.post<AuthResponse>('/api/auth/token', formData)
    const { access_token } = response.data
    
    // Сохраняем токен в localStorage
    localStorage.setItem('auth_token', access_token)
    
    // Декодируем токен для получения данных пользователя
    const decoded = jwtDecode<DecodedToken>(access_token)
    
    const user: User = {
      id: decoded.sub,
      username: decoded.username,
      email: decoded.email,
      role: decoded.role
    }
    
    return user
  } catch (error) {
    console.error('Ошибка при авторизации:', error)
    throw new Error('Неверное имя пользователя или пароль')
  }
}

/**
 * Выход пользователя
 */
export const logout = (): void => {
  localStorage.removeItem('auth_token')
  window.location.href = '/login'
}

/**
 * Проверка авторизации пользователя
 * @returns Объект с флагом авторизации и данными пользователя
 */
export const checkAuth = (): { isAuthenticated: boolean; user: User | null } => {
  const token = localStorage.getItem('auth_token')
  
  if (!token) {
    return { isAuthenticated: false, user: null }
  }
  
  try {
    const decoded = jwtDecode<DecodedToken>(token)
    
    // Проверяем срок действия токена
    const currentTime = Date.now() / 1000
    if (decoded.exp < currentTime) {
      localStorage.removeItem('auth_token')
      return { isAuthenticated: false, user: null }
    }
    
    const user: User = {
      id: decoded.sub,
      username: decoded.username,
      email: decoded.email,
      role: decoded.role
    }
    
    return { isAuthenticated: true, user }
  } catch (error) {
    localStorage.removeItem('auth_token')
    return { isAuthenticated: false, user: null }
  }
} 