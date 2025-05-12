import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Путь к директории с логами
log_dir = Path(__file__).parent / "logs"
log_file = log_dir / "app.log"

# Создаем директорию для логов, если она не существует
os.makedirs(log_dir, exist_ok=True)

# Форматтер для логов
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Настройка файлового обработчика с ротацией
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10485760,  # 10 МБ
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Настройка консольного обработчика
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Получение корневого логгера
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Очищаем существующие обработчики
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Добавляем новые обработчики
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Функция для получения логгера с правильной конфигурацией
def get_logger(name: str) -> logging.Logger:
    """
    Возвращает настроенный логгер с указанным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    return logger 