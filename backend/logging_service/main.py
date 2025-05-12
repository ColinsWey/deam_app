import os
import logging
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import aiofiles
from typing import List, Dict, Any, Optional
import datetime

from .logger import get_logger, log_file
from .schemas import LogResponse, ClearLogsResponse, HealthResponse, ServiceInfoResponse

# Получаем логгер для этого файла
logger = get_logger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Logging Service",
    description="Сервис для работы с логами приложения",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=ServiceInfoResponse)
async def root():
    """
    Корневой эндпоинт, возвращает информацию о сервисе
    """
    return ServiceInfoResponse(
        service="DemandForecastApp Logging Service",
        version="0.1.0",
        status="running"
    )

@app.get("/logs", response_model=LogResponse)
async def get_logs(lines: Optional[int] = Query(100, description="Количество последних строк логов для получения")):
    """
    Получить последние строки из файла логов
    
    Args:
        lines: Количество последних строк логов для получения
        
    Returns:
        LogResponse: Данные логов
    """
    try:
        if not log_file.exists():
            return LogResponse(logs=[], total_lines=0, returned_lines=0)
        
        # Ограничиваем максимальное количество строк
        if lines > 10000:
            lines = 10000
        elif lines < 1:
            lines = 1
        
        # Читаем файл логов с конца
        log_entries = []
        
        async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
            # Для больших файлов оптимизируем чтение с конца
            all_lines = await f.readlines()
            total_lines = len(all_lines)
            
            # Получаем последние N строк
            last_lines = all_lines[-lines:] if total_lines > lines else all_lines
            
            for line in last_lines:
                line = line.strip()
                if line:
                    log_entries.append(line)
        
        logger.info(f"Получено {len(log_entries)} строк логов")
        
        return LogResponse(
            logs=log_entries,
            total_lines=total_lines,
            returned_lines=len(log_entries)
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при получении логов: {str(e)}")

@app.post("/logs/clear", response_model=ClearLogsResponse)
async def clear_logs():
    """
    Очистить файл логов
    
    Returns:
        ClearLogsResponse: Результат операции
    """
    try:
        if log_file.exists():
            # Создаем резервную копию перед очисткой
            backup_file = log_file.with_suffix(f".backup.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.log")
            
            async with aiofiles.open(log_file, "r", encoding="utf-8") as src:
                content = await src.read()
                
                async with aiofiles.open(backup_file, "w", encoding="utf-8") as dst:
                    await dst.write(content)
            
            # Очищаем файл логов
            async with aiofiles.open(log_file, "w", encoding="utf-8") as f:
                await f.write("")
            
            logger.info(f"Логи очищены. Создана резервная копия: {backup_file.name}")
            
            return ClearLogsResponse(
                status="success",
                message=f"Логи очищены. Создана резервная копия: {backup_file.name}"
            )
        else:
            return ClearLogsResponse(
                status="success",
                message="Файл логов не существует"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при очистке логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке логов: {str(e)}")

@app.get("/logs/download")
async def download_logs():
    """
    Скачать файл логов
    
    Returns:
        FileResponse: Файл логов для скачивания
    """
    try:
        if not log_file.exists():
            raise HTTPException(status_code=404, detail="Файл логов не найден")
        
        logger.info(f"Запрошено скачивание файла логов: {log_file}")
        
        return FileResponse(
            path=log_file,
            filename="app.log",
            media_type="text/plain"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при скачивании логов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при скачивании логов: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка работоспособности сервиса
    
    Returns:
        HealthResponse: Статус сервиса
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.datetime.now()
    )

# Пример логирования при запуске
logger.info("Logging Service запущен")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True) 