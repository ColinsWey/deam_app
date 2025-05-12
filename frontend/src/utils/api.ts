import axios from 'axios'

// Настройка базового URL API
axios.defaults.baseURL = import.meta.env.VITE_API_URL || ''

// Добавляем перехватчик для обработки ошибок
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    
    if (response) {
      // Обработка ошибок авторизации
      if (response.status === 401) {
        // Если токен истек, перенаправляем на страницу входа
        window.location.href = '/login'
      }
      
      // Возвращаем понятное сообщение об ошибке
      return Promise.reject({
        status: response.status,
        message: response.data?.detail || 'Произошла ошибка при выполнении запроса',
        data: response.data
      })
    }
    
    return Promise.reject({
      message: error.message || 'Сетевая ошибка',
      status: 0
    })
  }
)

// Добавляем перехватчик для добавления токена авторизации к запросам
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  return config
})

export default axios 