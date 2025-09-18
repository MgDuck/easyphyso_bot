#!/usr/bin/env python3
"""
Конфигурация Telegram бота для PhySO
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# PhySO API настройки
PHYSO_API_BASE_URL = os.getenv("PHYSO_API_BASE_URL", "http://localhost:53251/api/v1")
PHYSO_API_CONNECT_TIMEOUT = int(os.getenv("PHYSO_API_CONNECT_TIMEOUT", "15"))
PHYSO_API_READ_TIMEOUT = int(os.getenv("PHYSO_API_READ_TIMEOUT", "600"))
PHYSO_API_STATUS_TIMEOUT = int(os.getenv("PHYSO_API_STATUS_TIMEOUT", "60"))

# Настройки кредитов
DEFAULT_CREDITS = 100  # Начальные кредиты для новых пользователей
MIN_CREDITS_FOR_PREDICTION = 10  # Минимум кредитов для предсказания

# Настройки PhySO по умолчанию
DEFAULT_EPOCHS = 50
DEFAULT_CONFIG = "config0"
DEFAULT_STOP_REWARD = 0.999

# Админы бота (Telegram user IDs)
ADMIN_IDS = [
    # 123456789,  # Добавьте свой Telegram ID
]

# Папки для файлов
UPLOAD_DIR = "data/uploads"
RESULTS_DIR = "data/results"

# Создаем папки если их нет
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Логирование
LOGGING_LEVEL = "INFO"
