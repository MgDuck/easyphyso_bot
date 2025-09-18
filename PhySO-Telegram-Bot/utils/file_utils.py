#!/usr/bin/env python3
"""
Утилиты для работы с файлами
"""
import os
import csv
import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from io import StringIO

logger = logging.getLogger(__name__)

def validate_csv_file(file_path: str) -> Dict[str, Any]:
    """Валидация CSV файла"""
    try:
        # Читаем CSV файл
        df = pd.read_csv(file_path)
        
        # Проверяем базовые требования
        if df.empty:
            return {"valid": False, "error": "Файл пустой"}
        
        if len(df.columns) < 2:
            return {"valid": False, "error": "Файл должен содержать минимум 2 столбца (x и y)"}
        
        if len(df) < 3:
            return {"valid": False, "error": "Файл должен содержать минимум 3 строки данных"}
        
        # Проверяем, что все столбцы числовые (кроме возможных строковых названий)
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) < 2:
            return {"valid": False, "error": "Файл должен содержать минимум 2 числовых столбца"}
        
        # Проверяем на NaN значения
        if df.isnull().any().any():
            return {"valid": False, "error": "Файл содержит пустые значения"}
        
        return {
            "valid": True,
            "shape": df.shape,
            "columns": list(df.columns),
            "numeric_columns": list(numeric_columns),
            "suggested_y": df.columns[-1],  # Предполагаем последний столбец как y
            "suggested_x": list(df.columns[:-1])
        }
        
    except Exception as e:
        return {"valid": False, "error": f"Ошибка чтения файла: {str(e)}"}

def read_csv_content(file_path: str) -> Optional[str]:
    """Прочитать содержимое CSV файла как строку"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_path}: {e}")
        return None

def create_result_csv(prediction_result: Dict[str, Any], output_path: str) -> bool:
    """Создать CSV файл с результатами предсказания"""
    try:
        # Создаем DataFrame с результатами
        results_data = {
            "Parameter": [
                "Status",
                "Best Formula", 
                "R² Score",
                "Epochs Used",
                "Processing Time (ms)",
                "Pareto Solutions Count",
                "Total Cost",
                "Configuration Used"
            ],
            "Value": [
                prediction_result.get("status", "unknown"),
                prediction_result.get("best_formula", "N/A"),
                prediction_result.get("best_r2", "N/A"),
                prediction_result.get("epochs", "N/A"),
                prediction_result.get("process_time", "N/A"),
                prediction_result.get("pareto_count", "N/A"),
                prediction_result.get("total_cost", "N/A"),
                prediction_result.get("run_config", "N/A")
            ]
        }
        
        # Добавляем метаданные если есть
        if prediction_result.get("metadata"):
            metadata = prediction_result["metadata"]
            for key, value in metadata.items():
                results_data["Parameter"].append(f"Metadata: {key}")
                results_data["Value"].append(str(value))
        
        df = pd.DataFrame(results_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Результаты сохранены в {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания файла результатов: {e}")
        return False

def generate_sample_csv(output_path: str, data_type: str = "linear") -> bool:
    """Генерация примера CSV файла"""
    try:
        if data_type == "linear":
            # Простые линейные данные y = 2x + 1
            data = {
                "x": list(range(1, 11)),
                "y": [2*x + 1 for x in range(1, 11)]
            }
        elif data_type == "quadratic":
            # Квадратичные данные y = x²
            data = {
                "x": list(range(1, 11)), 
                "y": [x**2 for x in range(1, 11)]
            }
        elif data_type == "exponential":
            # Экспоненциальные данные y = 2^x
            data = {
                "x": list(range(1, 8)),
                "y": [2**x for x in range(1, 8)]
            }
        else:
            # По умолчанию линейные
            data = {
                "x": list(range(1, 11)),
                "y": [2*x + 1 for x in range(1, 11)]
            }
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Пример CSV файла создан: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания примера файла: {e}")
        return False

def clean_old_files(directory: str, max_age_hours: int = 24):
    """Очистка старых файлов"""
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Удален старый файл: {filename}")
                    
    except Exception as e:
        logger.error(f"Ошибка очистки файлов: {e}")

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Получить информацию о файле"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024*1024), 2),
            "modified": stat.st_mtime,
            "exists": True
        }
    except Exception:
        return {"exists": False}
