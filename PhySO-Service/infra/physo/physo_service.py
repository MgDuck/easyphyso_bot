#!/usr/bin/env python3
"""
PhySO Service - сервис для работы с символьной регрессией для биллинговой системы
"""

import pandas as pd
import numpy as np
import physo
import logging
import os
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PhySoService:
    """Сервис для работы с PhySO в биллинговой системе"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.configs = {
            'config0': physo.config.config0.config0,
            'config1': physo.config.config1.config1,
            'config2': physo.config.config2.config2
        }
        
        self.default_operations = [
            'add', 'sub', 'mul', 'div', 'sqrt', 
            'log', 'exp', 'n2', 'n3', 'inv'
        ]
        
        logger.info("PhySO Service инициализирован")
    
    async def train(self, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Запуск обучения PhySO
        
        Args:
            prediction_data: словарь с данными предсказания
            
        Returns:
            Словарь с результатами обучения
        """
        try:
            logger.info(f"Начало обучения PhySO с параметрами: {prediction_data}")
            
            # Подготовка данных
            from io import StringIO
            df = pd.read_csv(StringIO(prediction_data['input_data']))
            X, y = self._prepare_data(df, prediction_data)
            
            # Подготовка параметров
            physo_params = self._prepare_physo_params(X, y, prediction_data)
            
            # Запуск PhySO
            logger.info("Запуск PhySO...")
            best_expr, _ = physo.SR(**physo_params)
            
            # Обработка результатов
            results = self._process_results(best_expr, X, y)
            
            # Сохранение файлов результатов
            saved_files = self._save_results()
            pareto_csv = self._load_pareto_csv(saved_files)
            
            logger.info("Обучение PhySO завершено успешно")
            
            return make_json_serializable({
                'success': True,
                'message': 'Обучение завершено успешно',
                'best_formula': results['formula'],
                'best_r2': results['r2'],
                'pareto_count': results['pareto_count'],
                'metadata': results['metadata'],
                'pareto_csv': pareto_csv
            })
            
        except Exception as e:
            logger.error(f"Ошибка обучения PhySO: {e}")
            return {
                'success': False,
                'message': f'Ошибка обучения: {str(e)}',
                'best_formula': None,
                'best_r2': None,
                'pareto_count': 0,
                'metadata': {},
                'pareto_csv': None
            }
    
    def _prepare_data(self, df: pd.DataFrame, prediction_data: Dict[str, Any]) -> tuple:
        """Подготовка данных для PhySO"""
        
        y_name = prediction_data.get('y_name', 'y')
        x_names = prediction_data.get('x_names')
        
        # Проверяем наличие целевой переменной
        if y_name not in df.columns:
            raise ValueError(f"Столбец '{y_name}' не найден в данных")
        
        # Получаем целевую переменную
        y = df[y_name].values
        
        # Определяем входные переменные
        if x_names:
            # Используем указанные переменные
            missing_cols = [col for col in x_names if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Столбцы не найдены: {missing_cols}")
            X_df = df[x_names]
        else:
            # Используем все столбцы кроме целевого
            x_columns = [col for col in df.columns if col != y_name]
            if not x_columns:
                raise ValueError("Не найдены входные переменные")
            X_df = df[x_columns]
        
        # Удаляем NaN значения
        mask = ~(X_df.isnull().any(axis=1) | pd.isnull(y))
        X_clean = X_df[mask]
        y_clean = y[mask]
        
        if len(X_clean) == 0:
            raise ValueError("После удаления NaN значений данные пусты")
        
        # Преобразуем в формат PhySO (n_features, n_samples) и к float
        X = X_clean.values.T.astype(float)
        y = y_clean.astype(float)
        logger.info(f"Данные подготовлены: X={X.shape}, y={y.shape}")
        
        return X, y
    
    def _prepare_physo_params(self, X: np.ndarray, y: np.ndarray, prediction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка параметров для PhySO"""
        
        # Базовые параметры
        params = {
            'X': X,
            'y': y,
            'epochs': prediction_data.get('epochs', 50),
            'parallel_mode': False,  # Всегда False для локального запуска
            'stop_reward': prediction_data.get('stop_reward', 0.999)
        }
        
        # Имена переменных
        x_names = prediction_data.get('x_names')
        if x_names:
            params['X_names'] = x_names
        else:
            params['X_names'] = [f'x{i}' for i in range(X.shape[0])]
        
        params['y_name'] = prediction_data.get('y_name', 'y')
        
        # Операции
        op_names = prediction_data.get('op_names')
        if op_names:
            params['op_names'] = op_names
        else:
            params['op_names'] = self.default_operations
        
        # Свободные константы
        free_consts_names = prediction_data.get('free_consts_names')
        if free_consts_names:
            params['free_consts_names'] = free_consts_names
        
        # Конфигурация
        run_config = prediction_data.get('run_config', 'config0')
        if run_config in self.configs:
            params['run_config'] = self.configs[run_config]
        
        logger.info(f"Параметры PhySO подготовлены: {list(params.keys())}")
        
        return params
    
    def _process_results(self, best_expr, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Обработка результатов PhySO"""
        
        try:
            # Получаем формулу
            if hasattr(best_expr, 'get_infix_pretty'):
                formula = str(best_expr.get_infix_pretty())
            elif hasattr(best_expr, 'infix_pretty'):
                formula = str(best_expr.infix_pretty)
            else:
                formula = str(best_expr)
            
            # Вычисляем R²
            try:
                if hasattr(best_expr, '__call__'):
                    y_pred = best_expr(X)
                    r2 = 1 - np.var(y - y_pred) / np.var(y)
                else:
                    r2 = None
            except:
                r2 = None
            
            # Подсчитываем количество решений в парето-фронте
            pareto_count = 0
            if os.path.exists('SR_curves_pareto.csv'):
                try:
                    pareto_df = pd.read_csv('SR_curves_pareto.csv')
                    pareto_count = len(pareto_df)
                except:
                    pass
            
            # Метаданные
            metadata = {
                'formula_length': len(formula),
                'data_shape': f"{X.shape[0]}x{X.shape[1]}",
                'timestamp': datetime.now().isoformat(),
                'is_physical': getattr(best_expr, 'is_physical', None)
            }
            
            return {
                'formula': formula,
                'r2': r2,
                'pareto_count': pareto_count,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Ошибка обработки результатов: {e}")
            return {
                'formula': 'Не удалось получить формулу',
                'r2': None,
                'pareto_count': 0,
                'metadata': {'error': str(e)}
            }
    
    def _save_results(self) -> List[str]:
        """Сохранение файлов результатов"""
        saved_files: List[str] = []

        # Создаем папку для результатов
        os.makedirs('data', exist_ok=True)
        
        # Файлы, которые PhySO создает автоматически
        source_files = [
            'SR_curves_pareto.csv',
            'SR_curves_data.csv', 
            'SR.log'
        ]
        
        # Копируем файлы в папку результатов
        for filename in source_files:
            if os.path.exists(filename):
                dest_path = f'data/{filename}'
                try:
                    shutil.copy2(filename, dest_path)
                    saved_files.append(dest_path)
                    logger.info(f"Файл {filename} сохранен в {dest_path}")
                except Exception as e:
                    logger.warning(f"Не удалось скопировать {filename}: {e}")
        return saved_files

    def _load_pareto_csv(self, saved_files: List[str]) -> Optional[Dict[str, Any]]:
        """Возвращает содержимое сохраненного SR_curves_pareto.csv."""
        target_path = os.path.join('data', 'SR_curves_pareto.csv')
        if target_path not in saved_files and not os.path.exists(target_path):
            return None

        try:
            with open(target_path, 'r', encoding='utf-8') as csv_file:
                content = csv_file.read()
            return {
                'filename': 'SR_curves_pareto.csv',
                'path': target_path,
                'content': content,
                'content_type': 'text/csv'
            }
        except Exception as exc:
            logger.warning(f"Не удалось прочитать {target_path}: {exc}")
            return None
    
    def get_available_configs(self) -> List[str]:
        """Получить список доступных конфигураций"""
        return list(self.configs.keys())
    
    def get_default_operations(self) -> List[str]:
        """Получить список операций по умолчанию"""
        return self.default_operations.copy()
    
    def calculate_cost(self, base_price: float, epoch_price: float, epochs: int) -> float:
        """Рассчитать стоимость выполнения PhySO"""
        return base_price + (epoch_price * epochs)


def make_json_serializable(obj):
    """Рекурсивно приводит вложенные структуры к типам, которые понимает JSON."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(make_json_serializable(v) for v in obj)
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (bool, int, float, str)) or obj is None:
        return obj
    return str(obj)
