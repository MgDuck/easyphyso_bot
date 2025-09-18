#!/usr/bin/env python3
"""
PhySO Telegram Bot - главный файл
"""
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config.settings import BOT_TOKEN, LOGGING_LEVEL
from handlers.commands import (
    start_command, help_command, add_credits_command,
    stats_command, sample_command, button_callback, admin_stats_command
)
from handlers.file_handlers import handle_document, epochs_callback

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOGGING_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    
    # Проверяем токен
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Не установлен BOT_TOKEN!")
        logger.info("📝 Создайте .env файл с вашим токеном бота")
        logger.info("💡 Получить токен можно у @BotFather в Telegram")
        return
    
    logger.info("🚀 Запуск PhySO Telegram Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_credits", add_credits_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("sample", sample_command))
    
    # Админские команды
    application.add_handler(CommandHandler("admin_stats", admin_stats_command))
    
    # Обработчики файлов
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Обработчики callback кнопок
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r"^(add_credits|stats|sample|add_\d+)$"))
    application.add_handler(CallbackQueryHandler(epochs_callback, pattern=r"^(epochs_|custom_|config_)"))
    
    # Обработчик неизвестных сообщений
    async def unknown_message(update: Update, context):
        await update.message.reply_text(
            "🤔 Я понимаю только команды и CSV файлы.\n\n"
            "📋 Используйте /help для справки\n"
            "📊 Или отправьте CSV файл для анализа"
        )
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
    
    # Запускаем бота
    logger.info("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
