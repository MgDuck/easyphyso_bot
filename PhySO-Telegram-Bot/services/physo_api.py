#!/usr/bin/env python3
"""Сервис для работы с PhySO API."""

import asyncio
import logging
from typing import Optional, Dict, Any, List

import requests

from config.settings import (
    PHYSO_API_BASE_URL,
    PHYSO_API_CONNECT_TIMEOUT,
    PHYSO_API_READ_TIMEOUT,
    PHYSO_API_STATUS_TIMEOUT,
)

logger = logging.getLogger(__name__)

class PhySoAPIService:
    """Сервис для работы с PhySO API.

    Блокирующие HTTP-запросы выполняются в пуле потоков, чтобы не блокировать
    event loop Telegram бота.
    """

    def __init__(self):
        self.base_url = PHYSO_API_BASE_URL.rstrip('/')
        self._request_timeout = (PHYSO_API_CONNECT_TIMEOUT, PHYSO_API_READ_TIMEOUT)
        self._status_timeout = (PHYSO_API_CONNECT_TIMEOUT, PHYSO_API_STATUS_TIMEOUT)

    async def get_user_balance(self, user_id: int, api_key: str) -> Optional[float]:
        return await asyncio.to_thread(self._get_user_balance_sync, user_id, api_key)

    async def create_prediction(
        self,
        user_id: int,
        api_key: str,
        csv_data: str,
        epochs: int = 50,
        config: str = "config0",
    ) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(
            self._create_prediction_sync,
            user_id,
            api_key,
            csv_data,
            epochs,
            config,
        )

    async def get_prediction_status(self, prediction_uuid: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_prediction_status_sync, prediction_uuid)

    async def get_user_predictions(self, user_id: int, api_key: str) -> Optional[List[Dict[str, Any]]]:
        return await asyncio.to_thread(self._get_user_predictions_sync, user_id, api_key)

    # --- Синхронные реализации ---

    def _get_user_balance_sync(self, user_id: int, api_key: str) -> Optional[float]:
        try:
            url = f"{self.base_url}/users/{user_id}/balance"
            headers = {"X-API-KEY": api_key}

            response = requests.get(url, headers=headers, timeout=self._status_timeout)
            if response.status_code == 200:
                return response.json().get("balance")

            logger.error(
                "Ошибка получения баланса: %s - %s", response.status_code, response.text[:200]
            )
            return None
        except requests.RequestException as exc:
            logger.error(f"Ошибка запроса баланса: {exc}")
            return None

    def _create_prediction_sync(
        self,
        user_id: int,
        api_key: str,
        csv_data: str,
        epochs: int,
        config: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/predictions/"
            headers = {
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            }

            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV файл должен содержать заголовок и данные")

            columns = [col.strip() for col in lines[0].split(',')]
            y_name = columns[-1]
            x_names = columns[:-1] if len(columns) > 1 else ["x"]

            payload = {
                "user_id": user_id,
                "input_data": csv_data,
                "y_name": y_name,
                "x_names": x_names,
                "epochs": epochs,
                "run_config": config,
                "stop_reward": 0.999,
                "parallel_mode": False,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=self._request_timeout)
            if response.status_code in (200, 202):
                return response.json()

            logger.error(
                "Ошибка создания предсказания: %s - %s", response.status_code, response.text[:500]
            )
            return None
        except (requests.RequestException, ValueError) as exc:
            logger.error(f"Ошибка запроса предсказания: {exc}")
            return None

    def _get_prediction_status_sync(self, prediction_uuid: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/predictions/{prediction_uuid}"
            response = requests.get(url, timeout=self._status_timeout)
            if response.status_code == 200:
                return response.json()

            logger.error(
                "Ошибка получения статуса предсказания: %s - %s",
                response.status_code,
                response.text[:200],
            )
            return None
        except requests.RequestException as exc:
            logger.error(f"Ошибка запроса статуса: {exc}")
            return None

    def _get_user_predictions_sync(self, user_id: int, api_key: str) -> Optional[List[Dict[str, Any]]]:
        try:
            url = f"{self.base_url}/predictions/user/{user_id}"
            headers = {"X-API-KEY": api_key}
            response = requests.get(url, headers=headers, timeout=self._status_timeout)

            if response.status_code == 200:
                return response.json()

            logger.error(
                "Ошибка получения предсказаний: %s - %s", response.status_code, response.text[:200]
            )
            return None
        except requests.RequestException as exc:
            logger.error(f"Ошибка запроса предсказаний: {exc}")
            return None
