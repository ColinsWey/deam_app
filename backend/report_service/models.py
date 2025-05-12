from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .database import Base

class ReportType(enum.Enum):
    """Тип отчета"""
    PDF = "pdf"
    XLSX = "xlsx"

class ReportTemplate(Base):
    """Модель шаблонов отчетов"""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    type = Column(SQLEnum(ReportType), nullable=False)
    template_path = Column(String, nullable=False)  # Путь к файлу шаблона (Jinja2 для PDF или конфигурация для Excel)
    
    # Служебные поля
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Отношения
    reports = relationship("ReportHistory", back_populates="template")

    def __repr__(self):
        return f"<ReportTemplate(id={self.id}, name={self.name}, type={self.type})>"

class ReportHistory(Base):
    """Модель истории сгенерированных отчетов"""
    __tablename__ = "report_history"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id"))
    type = Column(SQLEnum(ReportType), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expired_at = Column(DateTime(timezone=True), nullable=True)  # Дата истечения срока хранения
    parameters = Column(JSON, nullable=True)  # Параметры, с которыми был создан отчет
    
    # Отношения
    template = relationship("ReportTemplate", back_populates="reports")

    def __repr__(self):
        return f"<ReportHistory(id={self.id}, file_name={self.file_name}, type={self.type})>" 