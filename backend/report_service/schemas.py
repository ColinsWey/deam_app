from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ReportType(str, Enum):
    """Тип отчета"""
    PDF = "pdf"
    XLSX = "xlsx"

class ReportRequestBase(BaseModel):
    """Базовая модель запроса отчета"""
    start_date: datetime = Field(..., description="Начальная дата для отчета")
    end_date: datetime = Field(..., description="Конечная дата для отчета")
    product_ids: Optional[List[int]] = Field(None, description="Список ID продуктов для фильтрации")
    include_historical_data: bool = Field(True, description="Включать ли исторические данные")
    include_forecast: bool = Field(True, description="Включать ли прогнозы")

class PDFReportRequest(ReportRequestBase):
    """Запрос на генерацию PDF-отчета"""
    template_name: Optional[str] = Field("default_pdf", description="Название шаблона отчета")
    title: Optional[str] = Field("Отчет по спросу", description="Заголовок отчета")
    include_charts: bool = Field(True, description="Включать ли графики")

class XLSXReportRequest(ReportRequestBase):
    """Запрос на генерацию XLSX-отчета"""
    template_name: Optional[str] = Field("default_xlsx", description="Название шаблона отчета")
    include_pivot_tables: bool = Field(True, description="Включать ли сводные таблицы")
    sheet_names: Optional[Dict[str, str]] = Field(None, description="Названия листов отчета")

class ReportTemplateCreate(BaseModel):
    """Модель для создания шаблона отчета"""
    name: str = Field(..., description="Название шаблона")
    description: Optional[str] = None
    type: ReportType = Field(..., description="Тип отчета (PDF/XLSX)")
    template_path: str = Field(..., description="Путь к файлу шаблона")
    is_active: bool = True

class ReportTemplateResponse(ReportTemplateCreate):
    """Модель ответа для шаблона отчета"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReportData(BaseModel):
    """Данные отчета"""
    type: ReportType
    file_name: str
    created_at: datetime
    size_bytes: int
    
    class Config:
        from_attributes = True

class ReportHistoryCreate(BaseModel):
    """Модель для создания записи истории отчетов"""
    file_name: str = Field(..., description="Имя файла отчета")
    file_path: str = Field(..., description="Путь к файлу отчета")
    template_id: Optional[int] = Field(None, description="ID использованного шаблона")
    type: ReportType = Field(..., description="Тип отчета")
    size_bytes: int = Field(..., description="Размер файла в байтах")
    expired_at: Optional[datetime] = Field(None, description="Дата истечения срока хранения")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметры отчета")

class ReportHistoryResponse(ReportHistoryCreate):
    """Модель ответа для истории отчетов"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReportMetrics(BaseModel):
    """Метрики отчетов"""
    total_reports: int
    pdf_reports: int
    xlsx_reports: int
    average_size_bytes: int
    most_popular_template: Optional[str] = None

class ReportForecastDataPoint(BaseModel):
    """Точка данных прогноза для отчета"""
    product_id: int
    product_name: str
    date: datetime
    forecasted_demand: float
    accuracy: Optional[float] = None
    status: str
    
    class Config:
        from_attributes = True

class ReportHistoricalDataPoint(BaseModel):
    """Точка исторических данных для отчета"""
    product_id: int
    product_name: str
    date: datetime
    actual_demand: float
    
    class Config:
        from_attributes = True 