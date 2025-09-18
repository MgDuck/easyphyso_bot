#!/usr/bin/env python3
"""
Скрипт запуска PhySO Telegram Bot
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from bot import main
    main()
