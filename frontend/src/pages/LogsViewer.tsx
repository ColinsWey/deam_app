import { useState, useEffect } from 'react'
import { ArrowPathIcon, ArrowDownTrayIcon, TrashIcon } from '@heroicons/react/24/outline'
import { getLogs, clearLogs, downloadLogs } from '@services/logsService'

interface Log {
  message: string;
}

const LogsViewer = () => {
  const [logs, setLogs] = useState<string[]>([])
  const [totalLines, setTotalLines] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [linesLimit, setLinesLimit] = useState(100)
  
  const fetchLogs = async () => {
    setIsLoading(true)
    try {
      const response = await getLogs(linesLimit)
      setLogs(response.logs)
      setTotalLines(response.total_lines)
    } catch (error) {
      console.error('Ошибка при получении логов:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleClearLogs = async () => {
    if (confirm('Вы уверены, что хотите очистить все логи?')) {
      try {
        await clearLogs()
        fetchLogs()
      } catch (error) {
        console.error('Ошибка при очистке логов:', error)
      }
    }
  }
  
  useEffect(() => {
    fetchLogs()
    // Обновляем логи каждые 30 секунд
    const interval = setInterval(() => {
      fetchLogs()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [linesLimit])
  
  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <h1 className="text-2xl font-bold">Системные логи</h1>
        
        <div className="flex flex-wrap gap-2">
          <select
            className="input"
            value={linesLimit}
            onChange={(e) => setLinesLimit(Number(e.target.value))}
          >
            <option value={50}>Последние 50 строк</option>
            <option value={100}>Последние 100 строк</option>
            <option value={500}>Последние 500 строк</option>
            <option value={1000}>Последние 1000 строк</option>
          </select>
          
          <button 
            className="btn btn-outline flex items-center"
            onClick={fetchLogs}
            disabled={isLoading}
          >
            <ArrowPathIcon className={`w-5 h-5 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
          
          <button 
            className="btn btn-outline flex items-center"
            onClick={() => downloadLogs()}
          >
            <ArrowDownTrayIcon className="w-5 h-5 mr-1" />
            Скачать
          </button>
          
          <button 
            className="btn bg-danger-600 text-white hover:bg-danger-700 flex items-center"
            onClick={handleClearLogs}
          >
            <TrashIcon className="w-5 h-5 mr-1" />
            Очистить
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <div className="text-sm text-gray-500">
            Всего строк: {totalLines} | Отображено: {logs.length}
          </div>
        </div>
        
        <div className="p-0">
          <pre className="block whitespace-pre overflow-x-auto bg-gray-900 text-gray-100 rounded-b-lg text-sm font-mono p-4 max-h-[70vh]">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="py-1">
                  {log}
                </div>
              ))
            ) : (
              <div className="text-gray-400">Логи отсутствуют или не загружены</div>
            )}
          </pre>
        </div>
      </div>
    </div>
  )
}

export default LogsViewer 