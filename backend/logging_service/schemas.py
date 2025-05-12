from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class LogEntry(BaseModel):
    """Модель для одной строки лога"""
    timestamp: datetime = Field(..., description="Время записи лога")
    level: str = Field(..., description="Уровень логирования")
    logger: str = Field(..., description="Название логгера")
    message: str = Field(..., description="Сообщение лога")

class LogResponse(BaseModel):
    """Модель ответа с логами"""
    logs: List[str] = Field(..., description="Список строк логов")
    total_lines: int = Field(..., description="Общее количество строк в файле логов")
    returned_lines: int = Field(..., description="Количество возвращенных строк")

class ClearLogsResponse(BaseModel):
    """Модель ответа на очистку логов"""
    status: str = Field(..., description="Статус операции")
    message: str = Field(..., description="Описание результата операции")

class HealthResponse(BaseModel):
    """Модель ответа для проверки работоспособности"""
    status: str = Field(..., description="Статус сервиса")
    timestamp: datetime = Field(..., description="Время проверки")

class ServiceInfoResponse(BaseModel):
    """Модель ответа с информацией о сервисе"""
    service: str = Field(..., description="Название сервиса")
    version: str = Field(..., description="Версия сервиса")
    status: str = Field(..., description="Статус сервиса") 