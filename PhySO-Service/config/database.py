#!/usr/bin/env python3
"""Простая конфигурация для SQLite-репозиториев."""

from infra.db.sqlite_repositories import (
    SQLiteUserRepository,
    SQLiteModelRepository,
    SQLitePredictionRepository,
    SQLiteTransactionRepository,
)


def get_repositories():
    """Возвращает используемые в сервисе репозитории (SQLite)."""
    return {
        'user_repo': SQLiteUserRepository(),
        'model_repo': SQLiteModelRepository(),
        'prediction_repo': SQLitePredictionRepository(),
        'transaction_repo': SQLiteTransactionRepository(),
    }
