#!/usr/bin/env python3
"""
Сервис для управления пользователями Telegram бота
"""
import csv
import json
import os
import logging
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from copy import deepcopy

from config.settings import DEFAULT_CREDITS

logger = logging.getLogger(__name__)

class UserService:
    """Сервис для управления пользователями бота.

    Экземпляр реализован как синглтон, чтобы все обработчики разделяли одно состояние
    и не перезаписывали `users.json` друг другу.
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, users_file: str = "data/users.json"):
        if getattr(self, "_initialized", False):
            return

        self.users_file = users_file
        self._lock = threading.RLock()
        self.users = self._load_users()
        self.credit_log_file = os.path.join(
            os.path.dirname(self.users_file), "credit_history.csv"
        )
        self._ensure_credit_log()
        self._initialized = True

    def _load_users(self) -> Dict[str, Any]:
        """Загрузить пользователей из файла"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Ошибка загрузки пользователей: {e}")
        return {}

    def _save_users(self):
        """Сохранить пользователей в файл"""
        try:
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения пользователей: {e}")

    def _ensure_credit_log(self):
        """Создать файл лога кредитов при первом запуске"""
        try:
            os.makedirs(os.path.dirname(self.credit_log_file), exist_ok=True)
            if not os.path.exists(self.credit_log_file):
                with open(self.credit_log_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "telegram_id", "delta", "new_balance"])
        except Exception as e:
            logger.error(f"Ошибка инициализации лога кредитов: {e}")

    def _append_credit_log(self, telegram_id: str, delta: int, new_balance: int):
        """Добавить запись об изменении баланса кредитов"""
        try:
            with open(self.credit_log_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.utcnow().isoformat(),
                    telegram_id,
                    delta,
                    new_balance,
                ])
        except Exception as e:
            logger.error(f"Ошибка записи лога кредитов: {e}")

    def _get_user_internal(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(telegram_id)

    def get_user(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            return deepcopy(user) if user else None

    def create_user(self, telegram_id: str, username: str = None, first_name: str = None) -> Dict[str, Any]:
        """Создать нового пользователя"""
        name = first_name or username or f"User_{telegram_id}"

        user_data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "name": name,
            "credits": DEFAULT_CREDITS,
            "total_predictions": 0,
            "created_at": datetime.utcnow().isoformat(),
            # PhySO API данные
            "physo_user_id": 1,  # Используем admin пользователя из PhySO сервиса
            "physo_api_key": "test-api-key-123"  # Используем тестовый ключ из PhySO сервиса
        }

        with self._lock:
            self.users[telegram_id] = user_data
            self._save_users()

        logger.info(f"Создан новый пользователь: {telegram_id}")
        return deepcopy(user_data)

    def get_or_create_user(self, telegram_id: str, username: str = None, first_name: str = None) -> Dict[str, Any]:
        """Получить существующего пользователя или создать нового"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            if user is not None:
                return deepcopy(user)

        return self.create_user(telegram_id, username, first_name)

    def add_credits(self, telegram_id: str, amount: int) -> Optional[Dict[str, Any]]:
        """Добавить кредиты пользователю"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            if not user:
                return None

            user["credits"] += amount
            self._save_users()
            self._append_credit_log(telegram_id, amount, user["credits"])

            logger.info(f"Добавлено {amount} кредитов пользователю {telegram_id}")
            return deepcopy(user)

    def spend_credits(self, telegram_id: str, amount: int) -> Optional[Dict[str, Any]]:
        """Потратить кредиты пользователя"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            if not user:
                return None

            if user["credits"] < amount:
                return None

            user["credits"] -= amount
            user["total_predictions"] += 1
            self._save_users()
            self._append_credit_log(telegram_id, -amount, user["credits"])

            logger.info(f"Потрачено {amount} кредитов пользователем {telegram_id}")
            return deepcopy(user)

    def get_credits(self, telegram_id: str) -> int:
        """Получить количество кредитов пользователя"""
        user = self.get_user(telegram_id)
        return user["credits"] if user else 0

    def get_stats(self, telegram_id: str) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        user = self.get_user(telegram_id)
        if user:
            return {
                "credits": user["credits"],
                "total_predictions": user["total_predictions"],
                "created_at": user["created_at"]
            }
        return {}

    def get_all_users_count(self) -> int:
        """Получить общее количество пользователей"""
        with self._lock:
            return len(self.users)

    def get_total_credits(self) -> int:
        """Получить общее количество кредитов всех пользователей"""
        with self._lock:
            return sum(user["credits"] for user in self.users.values())

    def save_user_file_info(self, telegram_id: str, file_info: Dict[str, Any]) -> bool:
        """Сохранить информацию о загруженном файле пользователя"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            if not user:
                return False

            user["last_file"] = file_info
            self._save_users()
            logger.info(f"Сохранена информация о файле для пользователя {telegram_id}")
            return True

    def get_user_file_info(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о последнем загруженном файле пользователя"""
        with self._lock:
            user = self._get_user_internal(telegram_id)
            if user and "last_file" in user:
                return deepcopy(user["last_file"])
        return None
