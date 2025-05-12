import os
import logging
import pandas as pd
import jinja2
import aiofiles
import tempfile
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import xlsxwriter
import json
from weasyprint import HTML

logger = logging.getLogger(__name__)

# Импортируем модели из других сервисов, используя прямой импорт между микросервисами
# В реальном окружении может потребоваться API-запрос или общая база данных
# Здесь мы используем прямой импорт для простоты
try:
    from import_service.models import Product, Order, OrderItem
    from forecast_service.models import Forecast, ForecastStatus
    direct_imports = True
except ImportError:
    logger.warning("Не удалось импортировать модели напрямую, будем использовать API или внешний источник данных")
    direct_imports = False


async def get_forecast_data(
    db: AsyncSession, 
    product_ids: Optional[List[int]], 
    start_date: datetime, 
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Получает данные прогнозов из базы данных или API
    
    Args:
        db: Сессия базы данных
        product_ids: Список ID продуктов для фильтрации (опционально)
        start_date: Начальная дата для выборки
        end_date: Конечная дата для выборки
        
    Returns:
        List[Dict[str, Any]]: Список прогнозов
    """
    forecast_data = []
    
    if direct_imports:
        try:
            # Прямое получение данных из базы
            query = select(Forecast).where(
                Forecast.date.between(start_date, end_date)
            )
            
            if product_ids:
                query = query.where(Forecast.product_id.in_(product_ids))
            
            result = await db.execute(query)
            forecasts = result.scalars().all()
            
            # Получаем информацию о продуктах
            product_ids_set = {forecast.product_id for forecast in forecasts}
            products_query = select(Product).where(Product.id.in_(product_ids_set))
            products_result = await db.execute(products_query)
            products = {p.id: p.name for p in products_result.scalars().all()}
            
            # Формируем данные для отчета
            for forecast in forecasts:
                forecast_data.append({
                    "product_id": forecast.product_id,
                    "product_name": products.get(forecast.product_id, f"Продукт {forecast.product_id}"),
                    "date": forecast.date,
                    "forecasted_demand": forecast.forecasted_demand,
                    "confidence_low": forecast.confidence_low,
                    "confidence_high": forecast.confidence_high,
                    "is_manual": forecast.is_manual_override,
                    "accuracy": forecast.accuracy,
                    "status": forecast.status.value if forecast.status else "unknown"
                })
        except Exception as e:
            logger.error(f"Ошибка при получении данных прогноза: {e}")
            # Продолжаем с пустым списком
    else:
        # Имитация данных для примера
        # В реальном приложении здесь был бы API-запрос к forecast_service
        logger.info("Используем тестовые данные для прогноза, так как прямой импорт недоступен")
        forecast_data = [
            {
                "product_id": 1,
                "product_name": "Тестовый продукт 1",
                "date": datetime(2023, 10, 1),
                "forecasted_demand": 150.0,
                "confidence_low": 120.0,
                "confidence_high": 180.0,
                "is_manual": False,
                "accuracy": 0.85,
                "status": "green"
            }
        ]
    
    return forecast_data


async def get_historical_data(
    db: AsyncSession, 
    product_ids: Optional[List[int]], 
    start_date: datetime, 
    end_date: datetime
) -> List[Dict[str, Any]]:
    """
    Получает исторические данные из базы данных или API
    
    Args:
        db: Сессия базы данных
        product_ids: Список ID продуктов для фильтрации (опционально)
        start_date: Начальная дата для выборки
        end_date: Конечная дата для выборки
        
    Returns:
        List[Dict[str, Any]]: Список исторических данных
    """
    historical_data = []
    
    if direct_imports:
        try:
            # Прямое получение данных из базы
            # Объединяем Order и OrderItem для получения исторических данных
            query = select(OrderItem, Order, Product).join(
                Order, OrderItem.order_id == Order.id
            ).join(
                Product, OrderItem.product_id == Product.id
            ).where(
                Order.order_date.between(start_date, end_date)
            )
            
            if product_ids:
                query = query.where(OrderItem.product_id.in_(product_ids))
            
            result = await db.execute(query)
            
            # Формируем исторические данные по продуктам
            order_items_data = {}
            for order_item, order, product in result:
                key = (product.id, order.order_date.date())
                if key not in order_items_data:
                    order_items_data[key] = {
                        "product_id": product.id,
                        "product_name": product.name,
                        "date": order.order_date,
                        "actual_demand": 0
                    }
                order_items_data[key]["actual_demand"] += order_item.quantity
            
            historical_data = list(order_items_data.values())
        except Exception as e:
            logger.error(f"Ошибка при получении исторических данных: {e}")
            # Продолжаем с пустым списком
    else:
        # Имитация данных для примера
        # В реальном приложении здесь был бы API-запрос к import_service
        logger.info("Используем тестовые данные для истории, так как прямой импорт недоступен")
        historical_data = [
            {
                "product_id": 1,
                "product_name": "Тестовый продукт 1",
                "date": datetime(2023, 9, 1),
                "actual_demand": 142.0
            },
            {
                "product_id": 1,
                "product_name": "Тестовый продукт 1",
                "date": datetime(2023, 9, 15),
                "actual_demand": 158.0
            }
        ]
    
    return historical_data


async def generate_pdf_report(
    template_path: Union[str, Path],
    output_path: Union[str, Path],
    context: Dict[str, Any]
) -> int:
    """
    Генерирует PDF-отчет на основе шаблона Jinja2 и данных
    
    Args:
        template_path: Путь к шаблону Jinja2
        output_path: Путь для сохранения PDF-файла
        context: Контекст с данными для отчета
        
    Returns:
        int: Размер сгенерированного файла в байтах
    """
    try:
        # Настраиваем окружение Jinja2
        templates_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        
        if not os.path.exists(template_path):
            # Если шаблона нет, используем базовый шаблон
            template_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{{ title }}</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .header { text-align: center; margin-bottom: 20px; }
                    .section { margin-top: 20px; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    .footer { margin-top: 30px; text-align: center; font-size: 0.8em; }
                    .green { color: green; }
                    .yellow { color: orange; }
                    .red { color: red; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{{ title }}</h1>
                    <p>Период: {{ start_date.strftime('%d.%m.%Y') }} - {{ end_date.strftime('%d.%m.%Y') }}</p>
                </div>
                
                {% if historical_data %}
                <div class="section">
                    <h2>Исторические данные</h2>
                    <table>
                        <tr>
                            <th>Продукт</th>
                            <th>Дата</th>
                            <th>Фактический спрос</th>
                        </tr>
                        {% for item in historical_data %}
                        <tr>
                            <td>{{ item.product_name }}</td>
                            <td>{{ item.date.strftime('%d.%m.%Y') }}</td>
                            <td>{{ item.actual_demand }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                {% endif %}
                
                {% if forecast_data %}
                <div class="section">
                    <h2>Прогноз спроса</h2>
                    <table>
                        <tr>
                            <th>Продукт</th>
                            <th>Дата</th>
                            <th>Прогноз</th>
                            <th>Доверительный интервал</th>
                            <th>Точность</th>
                            <th>Статус</th>
                        </tr>
                        {% for item in forecast_data %}
                        <tr>
                            <td>{{ item.product_name }}</td>
                            <td>{{ item.date.strftime('%d.%m.%Y') }}</td>
                            <td>{{ item.forecasted_demand }}</td>
                            <td>{{ item.confidence_low }} - {{ item.confidence_high }}</td>
                            <td>{{ "%.2f" % (item.accuracy * 100) }}%</td>
                            <td class="{{ item.status }}">{{ item.status.upper() }}</td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                {% endif %}
                
                <div class="footer">
                    <p>Отчет сгенерирован: {{ generation_time }}</p>
                </div>
            </body>
            </html>
            """
            # Создаем временный файл для шаблона
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
                tmp.write(template_content.encode('utf-8'))
                template_path = tmp.name
            
            # Обновляем директорию и файл шаблона
            templates_dir = os.path.dirname(template_path)
            template_file = os.path.basename(template_path)
        
        # Создаем окружение Jinja2
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=True
        )
        
        # Загружаем шаблон и рендерим HTML
        template = env.get_template(template_file)
        html_content = template.render(**context)
        
        # Преобразуем HTML в PDF
        async with aiofiles.tempfile.NamedTemporaryFile('w', delete=False) as tmp:
            await tmp.write(html_content)
            tmp_path = tmp.name
        
        # Генерируем PDF с WeasyPrint
        pdf = HTML(filename=tmp_path).write_pdf()
        
        # Записываем PDF в выходной файл
        async with aiofiles.open(output_path, 'wb') as f:
            await f.write(pdf)
        
        # Удаляем временный файл
        os.unlink(tmp_path)
        
        # Возвращаем размер файла
        file_stats = os.stat(output_path)
        return file_stats.st_size
    
    except Exception as e:
        logger.error(f"Ошибка при генерации PDF-отчета: {e}")
        raise


async def generate_xlsx_report(
    template_path: Union[str, Path],
    output_path: Union[str, Path],
    context: Dict[str, Any]
) -> int:
    """
    Генерирует Excel-отчет на основе шаблона и данных
    
    Args:
        template_path: Путь к файлу конфигурации шаблона Excel
        output_path: Путь для сохранения XLSX-файла
        context: Контекст с данными для отчета
        
    Returns:
        int: Размер сгенерированного файла в байтах
    """
    try:
        # Создаем DataFrame из данных
        forecast_df = None
        historical_df = None
        
        if context.get("forecast_data"):
            forecast_df = pd.DataFrame(context["forecast_data"])
        
        if context.get("historical_data"):
            historical_df = pd.DataFrame(context["historical_data"])
        
        # Настройки шаблона
        template_config = {}
        sheet_names = context.get("sheet_names", {})
        
        # Если файл шаблона существует, загружаем его
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template_config = json.load(f)
        
        # Создаем новую Excel-книгу
        workbook = xlsxwriter.Workbook(output_path)
        
        # Определяем форматы
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1,
        })
        
        date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})
        number_format = workbook.add_format({'num_format': '0.00'})
        
        # Статусные форматы
        green_format = workbook.add_format({'fg_color': '#C6EFCE', 'num_format': '0.00'})
        yellow_format = workbook.add_format({'fg_color': '#FFEB9C', 'num_format': '0.00'})
        red_format = workbook.add_format({'fg_color': '#FFC7CE', 'num_format': '0.00'})
        
        # Лист с историческими данными
        if historical_df is not None:
            # Добавляем лист исторических данных
            hist_sheet_name = sheet_names.get("historical", "Исторические данные")
            worksheet_hist = workbook.add_worksheet(hist_sheet_name)
            
            # Заголовок
            headers = ["ID продукта", "Наименование продукта", "Дата", "Фактический спрос"]
            for col, header in enumerate(headers):
                worksheet_hist.write(0, col, header, header_format)
            
            # Данные
            row = 1
            for _, item in historical_df.iterrows():
                worksheet_hist.write(row, 0, item["product_id"])
                worksheet_hist.write(row, 1, item["product_name"])
                worksheet_hist.write(row, 2, item["date"], date_format)
                worksheet_hist.write(row, 3, item["actual_demand"], number_format)
                row += 1
            
            # Автоматическая настройка ширины столбцов
            worksheet_hist.autofit()
        
        # Лист с прогнозами
        if forecast_df is not None:
            # Добавляем лист прогнозов
            forecast_sheet_name = sheet_names.get("forecast", "Прогноз спроса")
            worksheet_forecast = workbook.add_worksheet(forecast_sheet_name)
            
            # Заголовок
            headers = ["ID продукта", "Наименование продукта", "Дата", "Прогноз", "Нижняя граница", 
                      "Верхняя граница", "Точность", "Статус", "Ручная корректировка"]
            for col, header in enumerate(headers):
                worksheet_forecast.write(0, col, header, header_format)
            
            # Данные
            row = 1
            for _, item in forecast_df.iterrows():
                # Выбираем формат в зависимости от статуса
                fmt = number_format
                if "status" in item:
                    if item["status"] == "green":
                        fmt = green_format
                    elif item["status"] == "yellow":
                        fmt = yellow_format
                    elif item["status"] == "red":
                        fmt = red_format
                
                worksheet_forecast.write(row, 0, item["product_id"])
                worksheet_forecast.write(row, 1, item["product_name"])
                worksheet_forecast.write(row, 2, item["date"], date_format)
                worksheet_forecast.write(row, 3, item["forecasted_demand"], fmt)
                
                if "confidence_low" in item and pd.notna(item["confidence_low"]):
                    worksheet_forecast.write(row, 4, item["confidence_low"], number_format)
                
                if "confidence_high" in item and pd.notna(item["confidence_high"]):
                    worksheet_forecast.write(row, 5, item["confidence_high"], number_format)
                
                if "accuracy" in item and pd.notna(item["accuracy"]):
                    worksheet_forecast.write(row, 6, item["accuracy"], number_format)
                
                if "status" in item:
                    worksheet_forecast.write(row, 7, item["status"].upper())
                
                if "is_manual" in item:
                    worksheet_forecast.write(row, 8, "Да" if item["is_manual"] else "Нет")
                
                row += 1
            
            # Автоматическая настройка ширины столбцов
            worksheet_forecast.autofit()
        
        # Создаем сводные таблицы, если нужно
        if context.get("include_pivot_tables") and forecast_df is not None:
            # Лист со сводной таблицей
            pivot_sheet_name = sheet_names.get("pivot", "Сводные данные")
            worksheet_pivot = workbook.add_worksheet(pivot_sheet_name)
            
            # Создаем сводную таблицу
            if hasattr(forecast_df, "to_excel"):
                # Создаем временный эксель для сводной таблицы
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    temp_path = tmp.name
                
                # Сохраняем данные во временный файл
                with pd.ExcelWriter(temp_path, engine='xlsxwriter') as writer:
                    forecast_df.to_excel(writer, sheet_name="Data", index=False)
                
                # Получаем данные из временного файла
                pivot_data = pd.read_excel(temp_path, sheet_name="Data")
                
                # Группировка по продуктам и дате
                if not pivot_data.empty:
                    pivot = pivot_data.groupby(['product_name', pd.Grouper(key='date', freq='M')])['forecasted_demand'].sum().reset_index()
                    
                    # Записываем данные на лист
                    worksheet_pivot.write(0, 0, "Продукт", header_format)
                    worksheet_pivot.write(0, 1, "Месяц", header_format)
                    worksheet_pivot.write(0, 2, "Прогноз", header_format)
                    
                    row = 1
                    for _, item in pivot.iterrows():
                        worksheet_pivot.write(row, 0, item["product_name"])
                        worksheet_pivot.write(row, 1, item["date"], date_format)
                        worksheet_pivot.write(row, 2, item["forecasted_demand"], number_format)
                        row += 1
                
                # Удаляем временный файл
                os.unlink(temp_path)
            
            # Автоматическая настройка ширины столбцов
            worksheet_pivot.autofit()
        
        # Лист с информацией о генерации
        info_sheet_name = sheet_names.get("info", "Информация")
        worksheet_info = workbook.add_worksheet(info_sheet_name)
        
        # Заполняем информационный лист
        worksheet_info.write(0, 0, "Параметр", header_format)
        worksheet_info.write(0, 1, "Значение", header_format)
        
        row = 1
        worksheet_info.write(row, 0, "Начальная дата")
        worksheet_info.write(row, 1, context["start_date"], date_format)
        
        row += 1
        worksheet_info.write(row, 0, "Конечная дата")
        worksheet_info.write(row, 1, context["end_date"], date_format)
        
        row += 1
        worksheet_info.write(row, 0, "Дата генерации")
        worksheet_info.write(row, 1, context["generation_time"])
        
        row += 1
        worksheet_info.write(row, 0, "Количество продуктов")
        product_count = 0
        if forecast_df is not None:
            product_count = forecast_df["product_id"].nunique()
        worksheet_info.write(row, 1, product_count)
        
        # Автоматическая настройка ширины столбцов
        worksheet_info.autofit()
        
        # Сохраняем книгу
        workbook.close()
        
        # Возвращаем размер файла
        file_stats = os.stat(output_path)
        return file_stats.st_size
    
    except Exception as e:
        logger.error(f"Ошибка при генерации Excel-отчета: {e}")
        raise 