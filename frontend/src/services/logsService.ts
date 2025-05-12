import axios from 'axios'

export interface LogsResponse {
  logs: string[];
  total_lines: number;
  returned_lines: number;
}

export interface ClearLogsResponse {
  status: string;
  message: string;
}

/**
 * Получить логи системы
 * @param lines Количество строк для получения
 * @returns Объект с логами и метаданными
 */
export const getLogs = async (lines: number = 100): Promise<LogsResponse> => {
  const response = await axios.get<LogsResponse>(`/api/logs?lines=${lines}`)
  return response.data
}

/**
 * Очистить логи системы
 * @returns Ответ с результатом операции
 */
export const clearLogs = async (): Promise<ClearLogsResponse> => {
  const response = await axios.post<ClearLogsResponse>('/api/logs/clear')
  return response.data
}

/**
 * Скачать файл логов
 */
export const downloadLogs = (): void => {
  window.open('/api/logs/download', '_blank')
} 