import os
import logging
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Path as PathParam, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import aiofiles
import tempfile
import uuid
import sqlalchemy as sa

from .database import get_db, engine, Base
from .models import ReportTemplate, ReportType, ReportHistory
from .schemas import (
    PDFReportRequest,
    XLSXReportRequest,
    ReportData,
    ReportTemplateCreate,
    ReportTemplateResponse,
    ReportHistoryResponse,
    ReportMetrics
)
from .report_generator import (
    generate_pdf_report,
    generate_xlsx_report,
    get_forecast_data,
    get_historical_data
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(title="Report Service", version="0.1.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Директория для хранения временных отчетов
REPORTS_DIR = Path("./reports")

@app.on_event("startup")
async def startup_event():
    """Выполняется при запуске приложения"""
    # Создаем таблицы в базе данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем директорию для отчетов, если ее нет
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Создаем дефолтные шаблоны отчетов, если их нет
    await create_default_templates()
    
    logger.info("Приложение запущено, база данных инициализирована")

async def create_default_templates():
    """Создает дефолтные шаблоны отчетов"""
    async with AsyncSession(engine) as session:
        # Проверяем, существуют ли уже дефолтные шаблоны
        stmt = select(ReportTemplate).where(ReportTemplate.name == "default_pdf")
        result = await session.execute(stmt)
        default_pdf = result.scalars().first()
        
        if not default_pdf:
            # Создаем дефолтный шаблон PDF
            default_pdf = ReportTemplate(
                name="default_pdf",
                description="Дефолтный шаблон PDF отчета",
                type=ReportType.PDF,
                template_path="templates/pdf/default.html",
                is_active=True
            )
            session.add(default_pdf)
        
        # Проверяем наличие шаблона для Excel
        stmt = select(ReportTemplate).where(ReportTemplate.name == "default_xlsx")
        result = await session.execute(stmt)
        default_xlsx = result.scalars().first()
        
        if not default_xlsx:
            # Создаем дефолтный шаблон Excel
            default_xlsx = ReportTemplate(
                name="default_xlsx",
                description="Дефолтный шаблон Excel отчета",
                type=ReportType.XLSX,
                template_path="templates/xlsx/default.json",
                is_active=True
            )
            session.add(default_xlsx)
        
        await session.commit()
        logger.info("Дефолтные шаблоны отчетов созданы")

@app.post("/reports/pdf", response_model=ReportData)
async def create_pdf_report(
    request: PDFReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Генерирует PDF-отчет на основе данных о прогнозах и исторических данных
    
    Args:
        request: Параметры запроса
        background_tasks: Объект для фоновых задач
        db: Сессия SQLAlchemy
        
    Returns:
        ReportData: Метаданные созданного отчета
    """
    try:
        # Получаем шаблон отчета
        stmt = select(ReportTemplate).where(
            (ReportTemplate.name == request.template_name) & 
            (ReportTemplate.type == ReportType.PDF)
        )
        result = await db.execute(stmt)
        template = result.scalars().first()
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Шаблон отчета '{request.template_name}' не найден")
        
        # Подготавливаем данные для отчета
        forecast_data = None
        historical_data = None
        
        if request.include_forecast:
            forecast_data = await get_forecast_data(db, request.product_ids, request.start_date, request.end_date)
        
        if request.include_historical_data:
            historical_data = await get_historical_data(db, request.product_ids, request.start_date, request.end_date)
        
        # Генерируем уникальное имя файла
        file_name = f"report_pdf_{uuid.uuid4()}.pdf"
        file_path = REPORTS_DIR / file_name
        
        # Генерируем отчет
        file_size = await generate_pdf_report(
            template.template_path,
            file_path,
            {
                "title": request.title,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "forecast_data": forecast_data,
                "historical_data": historical_data,
                "include_charts": request.include_charts,
                "generation_time": datetime.now().isoformat()
            }
        )
        
        # Создаем запись в истории отчетов
        expired_at = datetime.now() + timedelta(hours=1)  # Срок хранения 1 час
        report_history = ReportHistory(
            file_name=file_name,
            file_path=str(file_path),
            template_id=template.id,
            type=ReportType.PDF,
            size_bytes=file_size,
            expired_at=expired_at,
            parameters={
                "template_name": request.template_name,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "product_ids": request.product_ids,
                "include_historical_data": request.include_historical_data,
                "include_forecast": request.include_forecast,
                "include_charts": request.include_charts,
                "title": request.title
            }
        )
        db.add(report_history)
        await db.commit()
        
        # Настраиваем фоновую задачу для удаления отчета через некоторое время
        background_tasks.add_task(delete_report_after_delay, file_path, 3600)  # Удаляем через 1 час
        
        return ReportData(
            type=ReportType.PDF,
            file_name=file_name,
            created_at=datetime.now(),
            size_bytes=file_size
        )
    
    except Exception as e:
        logger.error(f"Ошибка при генерации PDF-отчета: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/xlsx", response_model=ReportData)
async def create_xlsx_report(
    request: XLSXReportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Генерирует Excel-отчет на основе данных о прогнозах и исторических данных
    
    Args:
        request: Параметры запроса
        background_tasks: Объект для фоновых задач
        db: Сессия SQLAlchemy
        
    Returns:
        ReportData: Метаданные созданного отчета
    """
    try:
        # Получаем шаблон отчета
        stmt = select(ReportTemplate).where(
            (ReportTemplate.name == request.template_name) & 
            (ReportTemplate.type == ReportType.XLSX)
        )
        result = await db.execute(stmt)
        template = result.scalars().first()
        
        if not template:
            raise HTTPException(status_code=404, detail=f"Шаблон отчета '{request.template_name}' не найден")
        
        # Подготавливаем данные для отчета
        forecast_data = None
        historical_data = None
        
        if request.include_forecast:
            forecast_data = await get_forecast_data(db, request.product_ids, request.start_date, request.end_date)
        
        if request.include_historical_data:
            historical_data = await get_historical_data(db, request.product_ids, request.start_date, request.end_date)
        
        # Генерируем уникальное имя файла
        file_name = f"report_xlsx_{uuid.uuid4()}.xlsx"
        file_path = REPORTS_DIR / file_name
        
        # Генерируем отчет
        file_size = await generate_xlsx_report(
            template.template_path,
            file_path,
            {
                "start_date": request.start_date,
                "end_date": request.end_date,
                "forecast_data": forecast_data,
                "historical_data": historical_data,
                "include_pivot_tables": request.include_pivot_tables,
                "sheet_names": request.sheet_names,
                "generation_time": datetime.now().isoformat()
            }
        )
        
        # Создаем запись в истории отчетов
        expired_at = datetime.now() + timedelta(hours=1)  # Срок хранения 1 час
        report_history = ReportHistory(
            file_name=file_name,
            file_path=str(file_path),
            template_id=template.id,
            type=ReportType.XLSX,
            size_bytes=file_size,
            expired_at=expired_at,
            parameters={
                "template_name": request.template_name,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "product_ids": request.product_ids,
                "include_historical_data": request.include_historical_data,
                "include_forecast": request.include_forecast,
                "include_pivot_tables": request.include_pivot_tables,
                "sheet_names": request.sheet_names
            }
        )
        db.add(report_history)
        await db.commit()
        
        # Настраиваем фоновую задачу для удаления отчета через некоторое время
        background_tasks.add_task(delete_report_after_delay, file_path, 3600)  # Удаляем через 1 час
        
        return ReportData(
            type=ReportType.XLSX,
            file_name=file_name,
            created_at=datetime.now(),
            size_bytes=file_size
        )
    
    except Exception as e:
        logger.error(f"Ошибка при генерации Excel-отчета: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/download/{file_name}")
async def download_report(file_name: str = PathParam(..., description="Имя файла отчета")):
    """
    Скачивает сгенерированный отчет
    
    Args:
        file_name: Имя файла отчета
        
    Returns:
        FileResponse: Файл отчета
    """
    file_path = REPORTS_DIR / file_name
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Отчет не найден или был удален")
    
    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/octet-stream"
    )

@app.get("/reports/history", response_model=List[ReportHistoryResponse])
async def get_report_history(
    type: Optional[ReportType] = Query(None, description="Фильтр по типу отчета"),
    limit: int = Query(10, description="Максимальное количество записей"),
    offset: int = Query(0, description="Смещение для пагинации"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает историю созданных отчетов
    
    Args:
        type: Фильтр по типу отчета
        limit: Максимальное количество записей
        offset: Смещение для пагинации
        db: Сессия SQLAlchemy
        
    Returns:
        List[ReportHistoryResponse]: Список записей истории
    """
    try:
        # Формируем запрос с опциональным фильтром
        query = select(ReportHistory).order_by(ReportHistory.created_at.desc())
        
        if type is not None:
            query = query.where(ReportHistory.type == type)
        
        # Добавляем пагинацию
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        reports = result.scalars().all()
        
        return [ReportHistoryResponse.from_orm(report) for report in reports]
    
    except Exception as e:
        logger.error(f"Ошибка при получении истории отчетов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/metrics", response_model=ReportMetrics)
async def get_report_metrics(db: AsyncSession = Depends(get_db)):
    """
    Получает метрики по сгенерированным отчетам
    
    Args:
        db: Сессия SQLAlchemy
        
    Returns:
        ReportMetrics: Метрики отчетов
    """
    try:
        # Получаем общее количество отчетов
        total_query = select(ReportHistory)
        total_result = await db.execute(total_query)
        total_reports = len(total_result.scalars().all())
        
        # Получаем количество PDF-отчетов
        pdf_query = select(ReportHistory).where(ReportHistory.type == ReportType.PDF)
        pdf_result = await db.execute(pdf_query)
        pdf_reports = len(pdf_result.scalars().all())
        
        # Получаем количество Excel-отчетов
        xlsx_query = select(ReportHistory).where(ReportHistory.type == ReportType.XLSX)
        xlsx_result = await db.execute(xlsx_query)
        xlsx_reports = len(xlsx_result.scalars().all())
        
        # Вычисляем средний размер отчета
        size_query = select(ReportHistory.size_bytes)
        size_result = await db.execute(size_query)
        sizes = [size for size, in size_result]
        average_size = sum(sizes) // len(sizes) if sizes else 0
        
        # Получаем самый популярный шаблон
        if total_reports > 0:
            popular_template_query = select(
                ReportTemplate.name,
                sa.func.count(ReportHistory.id).label("count")
            ).join(
                ReportHistory, ReportHistory.template_id == ReportTemplate.id
            ).group_by(
                ReportTemplate.name
            ).order_by(
                sa.desc("count")
            ).limit(1)
            
            popular_result = await db.execute(popular_template_query)
            popular_template = next(popular_result)[0] if popular_result else None
        else:
            popular_template = None
        
        return ReportMetrics(
            total_reports=total_reports,
            pdf_reports=pdf_reports,
            xlsx_reports=xlsx_reports,
            average_size_bytes=average_size,
            most_popular_template=popular_template
        )
    
    except Exception as e:
        logger.error(f"Ошибка при получении метрик отчетов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/templates", response_model=ReportTemplateResponse)
async def create_report_template(
    template: ReportTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создает новый шаблон отчета
    
    Args:
        template: Данные шаблона
        db: Сессия SQLAlchemy
        
    Returns:
        ReportTemplateResponse: Созданный шаблон
    """
    try:
        # Проверяем, что название шаблона уникально
        stmt = select(ReportTemplate).where(ReportTemplate.name == template.name)
        result = await db.execute(stmt)
        existing_template = result.scalars().first()
        
        if existing_template:
            raise HTTPException(status_code=400, detail=f"Шаблон с названием '{template.name}' уже существует")
        
        # Создаем новый шаблон
        new_template = ReportTemplate(
            name=template.name,
            description=template.description,
            type=template.type,
            template_path=template.template_path,
            is_active=template.is_active
        )
        
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        return ReportTemplateResponse.from_orm(new_template)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании шаблона отчета: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/templates", response_model=List[ReportTemplateResponse])
async def list_report_templates(
    type: Optional[ReportType] = Query(None, description="Фильтр по типу отчета"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активным шаблонам"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает список шаблонов отчетов
    
    Args:
        type: Фильтр по типу отчета
        is_active: Фильтр по активным шаблонам
        db: Сессия SQLAlchemy
        
    Returns:
        List[ReportTemplateResponse]: Список шаблонов
    """
    try:
        # Формируем запрос с опциональными фильтрами
        query = select(ReportTemplate)
        
        if type is not None:
            query = query.where(ReportTemplate.type == type)
        
        if is_active is not None:
            query = query.where(ReportTemplate.is_active == is_active)
        
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return [ReportTemplateResponse.from_orm(template) for template in templates]
    
    except Exception as e:
        logger.error(f"Ошибка при получении списка шаблонов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cleanup/expired", response_model=Dict[str, Any])
async def cleanup_expired_reports(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Запускает очистку истекших отчетов
    
    Args:
        background_tasks: Объект для фоновых задач
        db: Сессия SQLAlchemy
        
    Returns:
        Dict[str, Any]: Результат операции
    """
    try:
        # Находим все истекшие отчеты
        now = datetime.now()
        query = select(ReportHistory).where(
            (ReportHistory.expired_at < now) & 
            (ReportHistory.expired_at.is_not(None))
        )
        result = await db.execute(query)
        expired_reports = result.scalars().all()
        
        # Запускаем очистку в фоновом режиме
        if expired_reports:
            background_tasks.add_task(cleanup_expired_report_files, expired_reports, db)
            return {
                "status": "success",
                "message": f"Запущена очистка {len(expired_reports)} истекших отчетов"
            }
        else:
            return {
                "status": "success",
                "message": "Нет истекших отчетов для очистки"
            }
    
    except Exception as e:
        logger.error(f"Ошибка при запуске очистки истекших отчетов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def cleanup_expired_report_files(expired_reports: List[ReportHistory], db: AsyncSession):
    """
    Удаляет файлы истекших отчетов
    
    Args:
        expired_reports: Список истекших отчетов
        db: Сессия базы данных
    """
    try:
        for report in expired_reports:
            file_path = Path(report.file_path)
            
            # Проверяем существование файла и удаляем его
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Удален истекший отчет: {file_path}")
            
            # Удаляем запись из базы данных
            await db.delete(report)
        
        # Фиксируем изменения в базе
        await db.commit()
        
        logger.info(f"Очистка истекших отчетов завершена: удалено {len(expired_reports)} файлов")
    
    except Exception as e:
        logger.error(f"Ошибка при очистке истекших отчетов: {e}")
        await db.rollback()

async def delete_report_after_delay(file_path: Path, delay_seconds: int):
    """
    Удаляет файл отчета после определенного времени
    
    Args:
        file_path: Путь к файлу
        delay_seconds: Задержка перед удалением в секундах
    """
    import asyncio
    
    try:
        await asyncio.sleep(delay_seconds)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Файл отчета {file_path.name} удален после истечения срока хранения")
    except Exception as e:
        logger.error(f"Ошибка при удалении файла отчета: {e}")

@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса
    
    Returns:
        dict: Статус сервиса
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=True) 