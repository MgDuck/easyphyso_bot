#!/usr/bin/env python3
"""
Обработчики файлов для Telegram бота
"""
import os
import tempfile
import logging
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services import user_service, physo_api_service
from utils.file_utils import validate_csv_file, read_csv_content
from config.settings import UPLOAD_DIR, RESULTS_DIR, DEFAULT_EPOCHS, MIN_CREDITS_FOR_PREDICTION

logger = logging.getLogger(__name__)

# Сервисы подключаются как синглтоны в services.__init__

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик загруженных документов"""
    user = update.effective_user
    telegram_id = str(user.id)
    document = update.message.document
    
    # Проверяем пользователя
    user_data = user_service.get_user(telegram_id)
    if not user_data:
        await update.message.reply_text("❌ Пользователь не найден. Используйте /start")
        return
    
    # Проверяем тип файла
    if not document.file_name.endswith('.csv'):
        await update.message.reply_text(
            "❌ Поддерживаются только CSV файлы!\n"
            "Используйте /sample для получения примера."
        )
        return
    
    # Проверяем размер файла (максимум 5MB)
    if document.file_size > 5 * 1024 * 1024:
        await update.message.reply_text("❌ Файл слишком большой. Максимум 5MB.")
        return
    
    # Проверяем кредиты
    if user_data['credits'] < MIN_CREDITS_FOR_PREDICTION:
        await update.message.reply_text(
            f"❌ Недостаточно кредитов!\n"
            f"Необходимо минимум {MIN_CREDITS_FOR_PREDICTION} кредитов.\n"
            f"Ваш баланс: {user_data['credits']} кредитов.\n\n"
            f"Используйте /add_credits для пополнения."
        )
        return
    
    await update.message.reply_text("📥 Загружаю файл...")
    
    try:
        # Скачиваем файл
        file = await context.bot.get_file(document.file_id)
        
        # Создаем файл в постоянной папке uploads
        import uuid
        filename = f"{telegram_id}_{uuid.uuid4().hex[:8]}.csv"
        tmp_path = os.path.join(UPLOAD_DIR, filename)
        await file.download_to_drive(tmp_path)
        
        # Валидируем файл
        validation = validate_csv_file(tmp_path)
        
        if not validation['valid']:
            os.unlink(tmp_path)
            await update.message.reply_text(f"❌ Ошибка в файле: {validation['error']}")
            return
        
        # Сохраняем информацию о файле в контекст пользователя и в user_service
        context.user_data['csv_file_path'] = tmp_path
        context.user_data['csv_validation'] = validation
        context.user_data['csv_filename'] = document.file_name
        
        # Также сохраняем в постоянном хранилище
        user_service.save_user_file_info(telegram_id, {
            'csv_file_path': tmp_path,
            'csv_validation': validation,
            'csv_filename': document.file_name
        })
        
        # Показываем информацию о файле и параметры
        info_text = f"""✅ <b>Файл успешно загружен!</b>

📊 <b>Информация о данных:</b>
• Размер: {validation['shape'][0]} строк, {validation['shape'][1]} столбцов
• Столбцы: {', '.join(validation['columns'])}
• Предполагаемая целевая переменная: <code>{validation['suggested_y']}</code>
• Входные переменные: <code>{', '.join(validation['suggested_x'])}</code>

💰 <b>Стоимость предсказания:</b>
Выберите количество эпох (больше = точнее, но дороже):"""
        
        # Создаем клавиатуру с выбором эпох
        keyboard = [
            [InlineKeyboardButton("⚡ 10 эпох (~2 кредита)", callback_data="epochs_10"),
             InlineKeyboardButton("🔥 20 эпох (~3 кредита)", callback_data="epochs_20")],
            [InlineKeyboardButton("💎 50 эпох (~6 кредитов)", callback_data="epochs_50"),
             InlineKeyboardButton("🚀 100 эпох (~11 кредитов)", callback_data="epochs_100")],
            [InlineKeyboardButton("⚙️ Настроить параметры", callback_data="custom_params")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(info_text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}")
        await update.message.reply_text(f"❌ Ошибка обработки файла: {str(e)}")
        
        # Удаляем временный файл в случае ошибки
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass

async def process_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE, epochs: int, config: str = "config0"):
    """Обработка предсказания PhySO"""
    query = update.callback_query
    telegram_id = str(update.effective_user.id)
    
    # Проверяем наличие файла в контексте или в постоянном хранилище
    csv_file_path = None
    if 'csv_file_path' in context.user_data:
        csv_file_path = context.user_data['csv_file_path']
    else:
        # Пытаемся восстановить из постоянного хранилища
        file_info = user_service.get_user_file_info(telegram_id)
        if file_info and os.path.exists(file_info['csv_file_path']):
            csv_file_path = file_info['csv_file_path']
            context.user_data['csv_file_path'] = csv_file_path
            context.user_data['csv_validation'] = file_info['csv_validation']
            context.user_data['csv_filename'] = file_info['csv_filename']
    
    if not csv_file_path or not os.path.exists(csv_file_path):
        await query.edit_message_text("❌ Файл не найден. Загрузите CSV файл заново.")
        return
    
    user_data = user_service.get_user(telegram_id)
    if not user_data:
        await query.edit_message_text("❌ Пользователь не найден.")
        return
    
    # Рассчитываем стоимость (упрощенная формула)
    base_costs = {"config0": 1, "config1": 2, "config2": 3}
    epoch_costs = {"config0": 0.1, "config1": 0.2, "config2": 0.3}
    
    total_cost = int(base_costs[config] + epoch_costs[config] * epochs)
    
    # Проверяем кредиты
    if user_data['credits'] < total_cost:
        await query.edit_message_text(
            f"❌ Недостаточно кредитов!\n"
            f"Необходимо: {total_cost} кредитов\n"
            f"У вас: {user_data['credits']} кредитов"
        )
        return
    
    await query.edit_message_text("🔄 Обрабатываю данные через PhySO...")
    
    try:
        # Читаем CSV файл
        csv_content = read_csv_content(context.user_data['csv_file_path'])
        if not csv_content:
            await query.edit_message_text("❌ Ошибка чтения файла")
            return
        
        # Отправляем запрос в PhySO API
        prediction_result = await physo_api_service.create_prediction(
            user_id=user_data['physo_user_id'],
            api_key=user_data['physo_api_key'],
            csv_data=csv_content,
            epochs=epochs,
            config=config
        )
        
        if not prediction_result:
            await query.edit_message_text("❌ Ошибка обращения к PhySO API")
            return

        # Списываем кредиты
        updated_user = user_service.spend_credits(telegram_id, total_cost)
        if not updated_user:
            await query.edit_message_text("❌ Ошибка списания кредитов")
            return
        
        # Формируем результат
        status = prediction_result.get('status', 'unknown')
        remaining_credits = updated_user['credits']
        prediction_result.setdefault('total_cost', total_cost)
        prediction_result.setdefault('epochs', epochs)
        prediction_result.setdefault('run_config', config)
        
        if status == 'completed':
            result_text = f"""✅ <b>Предсказание завершено!</b>

🧮 <b>Найденная формула:</b> <code>{prediction_result.get('best_formula', 'N/A')}</code>
📊 <b>Точность (R²):</b> {prediction_result.get('best_r2', 'N/A')}
⚡ <b>Эпох использовано:</b> {epochs}
⏱️ <b>Время обработки:</b> {prediction_result.get('process_time', 'N/A')} мс
🎯 <b>Парето-решений:</b> {prediction_result.get('pareto_count', 'N/A')}

💰 <b>Потрачено кредитов:</b> {total_cost}
💳 <b>Остаток:</b> {remaining_credits} кредитов

UUID: <code>{prediction_result.get('uuid', 'N/A')}</code>"""
        elif status == 'failed':
            result_text = f"""❌ <b>Предсказание не удалось</b>

Причина: {prediction_result.get('best_formula', 'Неизвестная ошибка')}

💰 <b>Потрачено кредитов:</b> {total_cost}
💳 <b>Остаток:</b> {remaining_credits} кредитов

Попробуйте:
• Увеличить количество эпох
• Проверить качество данных
• Использовать другую конфигурацию"""
        else:
            result_text = f"""⏳ <b>Предсказание в обработке</b>

Статус: {status}
UUID: <code>{prediction_result.get('uuid', 'N/A')}</code>

💰 <b>Потрачено кредитов:</b> {total_cost}
💳 <b>Остаток:</b> {remaining_credits} кредитов"""
        
        await query.edit_message_text(result_text, parse_mode='HTML')
        
        # Отправляем оригинальный SR_curves_pareto.csv, если он доступен
        pareto_csv = prediction_result.get('pareto_csv')
        if status == 'completed' and pareto_csv and pareto_csv.get('content'):
            try:
                buffer = io.BytesIO(pareto_csv['content'].encode('utf-8'))
                buffer.name = pareto_csv.get('filename', 'SR_curves_pareto.csv')
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=buffer,
                    filename=buffer.name,
                    caption="📈 Pareto-фронт от PhySO"
                )
            except Exception as e:
                logger.error(f"Ошибка отправки SR_curves_pareto.csv: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки предсказания: {e}")
        await query.edit_message_text(f"❌ Ошибка обработки: {str(e)}")
    
    finally:
        # Удаляем временный файл
        try:
            os.unlink(context.user_data['csv_file_path'])
            del context.user_data['csv_file_path']
        except:
            pass

# Обработчики кнопок выбора эпох
async def epochs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора количества эпох"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("epochs_"):
        epochs = int(query.data.split("_")[1])
        await process_prediction(update, context, epochs, "config0")
    
    elif query.data == "custom_params":
        # Показываем расширенные настройки
        keyboard = [
            [InlineKeyboardButton("Config0 (базовый)", callback_data="config_config0"),
             InlineKeyboardButton("Config1 (расширенный)", callback_data="config_config1")],
            [InlineKeyboardButton("Config2 (продвинутый)", callback_data="config_config2")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_epochs")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ <b>Выберите конфигурацию PhySO:</b>\n\n"
            "• <b>Config0</b> - базовая (быстро, дешево)\n"
            "• <b>Config1</b> - расширенная (средне)\n" 
            "• <b>Config2</b> - продвинутая (медленно, дорого)\n\n"
            "Затем выберите количество эпох.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data.startswith("config_"):
        config = query.data.split("_")[1]
        context.user_data['selected_config'] = config
        
        # Показываем выбор эпох для выбранной конфигурации
        costs = {"config0": "1+0.1", "config1": "2+0.2", "config2": "3+0.3"}
        
        keyboard = [
            [InlineKeyboardButton(f"10 эпох (~{int(1 + 0.1*10)} кредитов)", callback_data=f"custom_epochs_10"),
             InlineKeyboardButton(f"20 эпох (~{int(1 + 0.1*20)} кредитов)", callback_data=f"custom_epochs_20")],
            [InlineKeyboardButton(f"50 эпох (~{int(1 + 0.1*50)} кредитов)", callback_data=f"custom_epochs_50"),
             InlineKeyboardButton(f"100 эпох (~{int(1 + 0.1*100)} кредитов)", callback_data=f"custom_epochs_100")],
            [InlineKeyboardButton("🔙 Назад", callback_data="custom_params")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚡ <b>Выберите количество эпох для {config.upper()}:</b>\n\n"
            f"Формула стоимости: {costs[config]} кредитов за эпоху",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data.startswith("custom_epochs_"):
        epochs = int(query.data.split("_")[2])
        config = context.user_data.get('selected_config', 'config0')
        await process_prediction(update, context, epochs, config)
