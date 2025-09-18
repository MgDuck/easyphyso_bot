#!/usr/bin/env python3
"""
SQLite версии репозиториев для быстрого тестирования
"""
import sqlite3
import os
import sys
import json
from typing import Optional, List
from datetime import datetime

# Добавляем путь к проекту
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.entities.user import User
from core.entities.model import Model
from core.entities.prediction import Prediction
from core.entities.transaction import Transaction
from core.repositories.user_repository import UserRepository
from core.repositories.model_repository import ModelRepository
from core.repositories.prediction_repository import PredictionRepository
from core.repositories.transaction_repository import TransactionRepository

DB_PATH = os.path.join(project_root, "physo_billing.db")

def get_sqlite_connection():
    """Получение подключения к SQLite базе"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    return conn

class SQLiteUserRepository(UserRepository):
    """SQLite реализация UserRepository"""
    
    def add(self, user: User) -> User:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (name, telegram_id, balance, password_hash, api_key)
                VALUES (?, ?, ?, ?, ?)
            """, (user.name, user.telegram_id, user.balance, user.password_hash, user.api_key))
            user.id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'], name=row['name'], telegram_id=row['telegram_id'],
                    balance=row['balance'], password_hash=row['password_hash'], 
                    api_key=row['api_key'], created_at=row['created_at']
                )
        finally:
            conn.close()
        return None
    
    def get_by_api_key(self, api_key: str) -> Optional[User]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'], name=row['name'], telegram_id=row['telegram_id'],
                    balance=row['balance'], password_hash=row['password_hash'], 
                    api_key=row['api_key'], created_at=row['created_at']
                )
        finally:
            conn.close()
        return None
    
    def update_balance(self, user_id: int, new_balance: float) -> bool:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'], name=row['name'], telegram_id=row['telegram_id'],
                    balance=row['balance'], password_hash=row['password_hash'], 
                    api_key=row['api_key'], created_at=row['created_at']
                )
        finally:
            conn.close()
        return None
    
    def list_all(self) -> List[User]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users ORDER BY name")
            rows = cursor.fetchall()
            return [User(
                id=row['id'], name=row['name'], telegram_id=row['telegram_id'],
                balance=row['balance'], password_hash=row['password_hash'], 
                api_key=row['api_key'], created_at=row['created_at']
            ) for row in rows]
        finally:
            conn.close()
    
    def get_by_name(self, name: str) -> Optional[User]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'], name=row['name'], telegram_id=row['telegram_id'],
                    balance=row['balance'], password_hash=row['password_hash'], 
                    api_key=row['api_key'], created_at=row['created_at']
                )
        finally:
            conn.close()
        return None
    
    def update_password_hash(self, user_id: int, password_hash: str) -> bool:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def update_api_key(self, user_id: int, api_key: str) -> bool:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET api_key = ? WHERE id = ?", (api_key, user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

class SQLiteModelRepository(ModelRepository):
    """SQLite реализация ModelRepository"""
    
    def add(self, model: Model) -> Model:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO models (name, description, base_price, epoch_price, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (model.name, model.description, model.base_price, model.epoch_price, model.is_active))
            model.id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return model
    
    def get_by_id(self, model_id: int) -> Optional[Model]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            row = cursor.fetchone()
            if row:
                return Model(
                    id=row['id'], name=row['name'], description=row['description'],
                    base_price=row['base_price'], epoch_price=row['epoch_price'], 
                    is_active=bool(row['is_active'])
                )
        finally:
            conn.close()
        return None
    
    def get_active_model(self) -> Optional[Model]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return Model(
                    id=row['id'], name=row['name'], description=row['description'],
                    base_price=row['base_price'], epoch_price=row['epoch_price'], 
                    is_active=bool(row['is_active'])
                )
        finally:
            conn.close()
        return None
    
    def list_all(self) -> List[Model]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models ORDER BY name")
            rows = cursor.fetchall()
            return [Model(
                id=row['id'], name=row['name'], description=row['description'],
                base_price=row['base_price'], epoch_price=row['epoch_price'], 
                is_active=bool(row['is_active'])
            ) for row in rows]
        finally:
            conn.close()
    
    def get_by_name(self, name: str) -> Optional[Model]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM models WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return Model(
                    id=row['id'], name=row['name'], description=row['description'],
                    base_price=row['base_price'], epoch_price=row['epoch_price'], 
                    is_active=bool(row['is_active'])
                )
        finally:
            conn.close()
        return None

class SQLitePredictionRepository(PredictionRepository):
    """SQLite реализация PredictionRepository"""
    
    def add(self, prediction: Prediction) -> Prediction:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO predictions (
                    uuid, user_id, model_id, input_data, y_name, x_names,
                    epochs, op_names, free_consts_names, run_config, stop_reward,
                    parallel_mode, best_formula, best_r2, pareto_count, metadata,
                    total_cost, status, created_at, completed_at, queue_time, process_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.uuid, prediction.user_id, prediction.model_id,
                prediction.input_data, prediction.y_name,
                json.dumps(prediction.x_names) if prediction.x_names else None,
                prediction.epochs,
                json.dumps(prediction.op_names) if prediction.op_names else None,
                json.dumps(prediction.free_consts_names) if prediction.free_consts_names else None,
                prediction.run_config, prediction.stop_reward, prediction.parallel_mode,
                prediction.best_formula, prediction.best_r2, prediction.pareto_count,
                json.dumps(prediction.metadata) if prediction.metadata else None,
                prediction.total_cost, prediction.status, prediction.created_at,
                prediction.completed_at, prediction.queue_time, prediction.process_time
            ))
            prediction.id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return prediction
    
    def get_by_id(self, prediction_id: int) -> Optional[Prediction]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_prediction(row)
        finally:
            conn.close()
        return None
    
    def get_by_uuid(self, uuid: str) -> Optional[Prediction]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM predictions WHERE uuid = ?", (uuid,))
            row = cursor.fetchone()
            if row:
                return self._map_row_to_prediction(row)
        finally:
            conn.close()
        return None
    
    def update(self, prediction: Prediction) -> bool:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE predictions SET
                    input_data = ?, y_name = ?, x_names = ?, epochs = ?, op_names = ?,
                    free_consts_names = ?, run_config = ?, stop_reward = ?, parallel_mode = ?,
                    best_formula = ?, best_r2 = ?, pareto_count = ?, metadata = ?,
                    total_cost = ?, status = ?, completed_at = ?, queue_time = ?, process_time = ?
                WHERE id = ?
            """, (
                prediction.input_data, prediction.y_name,
                json.dumps(prediction.x_names) if prediction.x_names else None,
                prediction.epochs,
                json.dumps(prediction.op_names) if prediction.op_names else None,
                json.dumps(prediction.free_consts_names) if prediction.free_consts_names else None,
                prediction.run_config, prediction.stop_reward, prediction.parallel_mode,
                prediction.best_formula, prediction.best_r2, prediction.pareto_count,
                json.dumps(make_json_serializable(prediction.metadata)) if prediction.metadata else None,
                prediction.total_cost, prediction.status, prediction.completed_at,
                prediction.queue_time, prediction.process_time, prediction.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def list_by_user(self, user_id: int) -> List[Prediction]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [self._map_row_to_prediction(row) for row in rows]
        finally:
            conn.close()
    
    def _map_row_to_prediction(self, row) -> Prediction:
        """Маппинг строки БД в объект Prediction"""
        return Prediction(
            id=row['id'], uuid=row['uuid'], user_id=row['user_id'], model_id=row['model_id'],
            input_data=row['input_data'], y_name=row['y_name'],
            x_names=json.loads(row['x_names']) if row['x_names'] else None,
            epochs=row['epochs'],
            op_names=json.loads(row['op_names']) if row['op_names'] else None,
            free_consts_names=json.loads(row['free_consts_names']) if row['free_consts_names'] else None,
            run_config=row['run_config'], stop_reward=row['stop_reward'],
            parallel_mode=bool(row['parallel_mode']), best_formula=row['best_formula'],
            best_r2=row['best_r2'], pareto_count=row['pareto_count'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            total_cost=row['total_cost'], status=row['status'],
            created_at=row['created_at'], completed_at=row['completed_at'],
            queue_time=row['queue_time'], process_time=row['process_time']
        )

class SQLiteTransactionRepository(TransactionRepository):
    """SQLite реализация TransactionRepository"""
    
    def add(self, transaction: Transaction) -> Transaction:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO transactions (user_id, amount, description, prediction_id)
                VALUES (?, ?, ?, ?)
            """, (transaction.user_id, transaction.amount, transaction.description, transaction.prediction_id))
            transaction.id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()
        return transaction
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            if row:
                return Transaction(
                    id=row['id'], user_id=row['user_id'], amount=row['amount'],
                    description=row['description'], prediction_id=row['prediction_id'],
                    created_at=row['created_at']
                )
        finally:
            conn.close()
        return None
    
    def list_by_user(self, user_id: int) -> List[Transaction]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [Transaction(
                id=row['id'], user_id=row['user_id'], amount=row['amount'],
                description=row['description'], prediction_id=row['prediction_id'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            conn.close()

def make_json_serializable(obj):
    """Рекурсивно преобразует объект к сериализуемым типам для json.dumps"""
    import numpy as np
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(v) for v in obj)
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (bool, int, float, str)):
        return obj
    else:
        # Попробуем привести к строке
        return str(obj)
