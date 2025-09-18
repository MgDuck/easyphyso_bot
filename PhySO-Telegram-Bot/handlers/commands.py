#!/usr/bin/env python3
"""
Обработчики команд Telegram бота
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services import user_service
from config.settings import ADMIN_IDS

logger = logging.getLogger(__name__)

# Сервисы подключаются как синглтоны в services.__init__

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Создаем или получаем пользователя
    user_data = user_service.get_or_create_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name
    )
    
    welcome_text = f"""🚀 *Добро пожаловать в PhySO Bot\\!*

Привет, {user.first_name or user.username or 'друг'}\\! 

Этот бот поможет вам найти математические формулы из ваших данных используя символьную регрессию PhySO\\.

💰 *Ваш баланс:* {user_data['credits']} кредитов

📊 *Как это работает:*
1\\. Отправьте CSV файл с данными
2\\. Выберите количество эпох \\(влияет на стоимость\\)
3\\. Получите найденную формулу и результаты

💡 *Доступные команды:*
/add\\_credits \\- пополнить кредиты
/help \\- справка
/sample \\- получить пример CSV файла
/stats \\- ваша статистика

Отправьте CSV файл для начала работы\\!"""

    await update.message.reply_text(welcome_text, parse_mode='MarkdownV2')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """📖 <b>Справка по PhySO Bot</b>

<b>Основные команды:</b>
/start - начать работу с ботом
/add_credits - пополнить кредиты
/stats - ваша статистика
/sample - получить пример CSV файла

<b>Как использовать:</b>

1️⃣ <b>Подготовьте данные</b>
   • CSV файл с числовыми данными
   • Минимум 2 столбца (x и y)
   • Минимум 3 строки данных

2️⃣ <b>Отправьте файл</b>
   • Просто отправьте CSV файл в чат
   • Бот автоматически определит переменные

3️⃣ <b>Выберите параметры</b>
   • Количество эпох (больше = точнее, но дороже)
   • Конфигурация PhySO

4️⃣ <b>Получите результат</b>
   • Найденная формула
   • Точность (R²)
   • Pareto-кривые от PhySO

<b>Стоимость:</b>
• config0: 1 кредит + 0.1 за эпоху
• config1: 2 кредита + 0.2 за эпоху  
• config2: 3 кредита + 0.3 за эпоху

<b>Пример данных:</b>
<pre>
x,y
1,2
2,4
3,6
4,8
5,10
</pre>

Для получения примера файла используйте /sample"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

async def add_credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_credits"""
    keyboard = [
        [InlineKeyboardButton("🎁 +10 кредитов", callback_data="add_10"),
         InlineKeyboardButton("💎 +50 кредитов", callback_data="add_50")],
        [InlineKeyboardButton("🚀 +100 кредитов", callback_data="add_100"),
         InlineKeyboardButton("💰 +500 кредитов", callback_data="add_500")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """💳 *Пополнение кредитов*

Выберите количество кредитов для пополнения:

🎁 *10 кредитов* \\- для тестирования
💎 *50 кредитов* \\- для небольших проектов  
🚀 *100 кредитов* \\- для активного использования
💰 *500 кредитов* \\- для профессиональной работы

_В демо\\-версии пополнение бесплатное\\!_"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats"""
    telegram_id = str(update.effective_user.id)
    user_data = user_service.get_user(telegram_id)
    
    if user_data:
        stats_text = f"""📊 <b>Ваша статистика</b>

👤 <b>Профиль:</b>
• Имя: {user_data['name']}
• Telegram ID: {telegram_id}
• Дата регистрации: {user_data['created_at'][:10]}

💰 <b>Кредиты:</b>
• Текущий баланс: {user_data['credits']}
• Всего предсказаний: {user_data['total_predictions']}

🔧 <b>PhySO API:</b>
• User ID: {user_data['physo_user_id']}
• API Key: {user_data['physo_api_key'][:20]}...

📈 <b>Общая статистика:</b>
• Всего пользователей: {user_service.get_all_users_count()}
• Общий пул кредитов: {user_service.get_total_credits()}"""
        
        await update.message.reply_text(stats_text, parse_mode='HTML')
    else:
        await update.message.reply_text("❌ Статистика недоступна. Используйте /start")

async def sample_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /sample - отправка примера CSV файла"""
    from utils.file_utils import generate_sample_csv
    import tempfile
    import os
    
    # Создаем временный файл с примером
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    # Генерируем пример данных
    if generate_sample_csv(tmp_path, "linear"):
        try:
            # Отправляем файл
            with open(tmp_path, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename="sample_linear_data.csv",
                    caption="""📋 <b>Пример CSV файла</b>

Это пример линейных данных (y = 2x + 1).

Используйте такой формат:
• Первая строка - заголовки столбцов
• Числовые данные в каждой строке
• Минимум 2 столбца и 3 строки

Отправьте этот файл обратно для тестирования!""",
                    parse_mode='HTML'
                )
        finally:
            # Удаляем временный файл
            os.unlink(tmp_path)
    else:
        await update.message.reply_text("❌ Ошибка создания примера файла")

# Обработчики inline кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик inline кнопок"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(update.effective_user.id)
    
    if query.data == "add_credits":
        await add_credits_command(update, context)
    
    elif query.data == "stats":
        await stats_command(update, context)
    
    elif query.data == "sample":
        await sample_command(update, context)
    
    elif query.data.startswith("add_"):
        # Пополнение кредитов
        amount = int(query.data.split("_")[1])

        updated_user = user_service.add_credits(telegram_id, amount)
        if updated_user:
            await query.edit_message_text(
                f"✅ *Кредиты пополнены\\!*\n\n"
                f"Добавлено: \\+{amount} кредитов\n"
                f"Новый баланс: {updated_user['credits']} кредитов",
                parse_mode='MarkdownV2'
            )
        else:
            await query.edit_message_text("❌ Ошибка пополнения кредитов")

# Админские команды
async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админская команда - общая статистика"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У вас нет прав администратора")
        return
    
    total_users = user_service.get_all_users_count()
    total_credits = user_service.get_total_credits()
    
    admin_text = f"""🔧 *Админ панель*

👥 *Пользователи:* {total_users}
💰 *Общий пул кредитов:* {total_credits}

*Команды:*
/admin\\_add\\_credits @username amount \\- добавить кредиты
/admin\\_user\\_info @username \\- информация о пользователе"""
    
    await update.message.reply_text(admin_text, parse_mode='MarkdownV2')
