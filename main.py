import discord
from discord.ext import commands
from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
import re
from datetime import datetime
import pytz
import logging
import os  # Для использования переменных окружения

# Настройки
DISCORD_TOKEN = 'ODc1NDYwMzIxNDA4NTg5ODg0.GfMufu.cOVY83fJXTpn6glJwKqf4ZF6LKyI_dLpeyE988'  # Вставьте ваш реальный токен от Discord
TELEGRAM_TOKEN = '7747784908:AAFamlPM2xBi6TUbhpmlayik-SyhSm-JH44'  # Вставьте ваш реальный токен от Telegram
TELEGRAM_CHAT_ID = '-4583961509'  # Ваш реальный ID чата в Telegram
TARGET_CHANNEL_ID = 935772273590284338  # ID канала, за которым нужно следить


# Словарь с часовыми поясами пользователей
user_timezones = {
    # Пример: ID пользователя: часовой пояс
}

# Создание объектов ботов
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

discord_bot = commands.Bot(command_prefix='!', intents=intents)

# Настройка логирования
logging.basicConfig(level=logging.INFO)


@discord_bot.event
async def on_ready():
    print(f'We have logged in as {discord_bot.user}')


def get_user_timezone(user_id):
    return user_timezones.get(user_id, 'UTC')  # По умолчанию UTC


@discord_bot.command()
async def set_timezone(ctx, timezone: str):
    """Устанавливает часовой пояс пользователя."""
    try:
        # Проверка валидности часового пояса
        pytz.timezone(timezone)
        user_timezones[ctx.author.id] = timezone
        await ctx.send(f"Ваш часовой пояс установлен на: {timezone}")
    except pytz.UnknownTimeZoneError:
        await ctx.send("Неверный часовой пояс. Пожалуйста, введите правильный.")


@discord_bot.event
async def on_message(message):
    if message.author == discord_bot.user:
        return

    if message.channel.id != TARGET_CHANNEL_ID:
        return

    text = message.content
    for mention in message.mentions:
        text = text.replace(f"<@{mention.id}>", mention.display_name)
    for role in message.role_mentions:
        text = text.replace(f"<@&{role.id}>", role.name)

    def format_timestamp(match):
        timestamp = int(match.group(1))
        user_tz = get_user_timezone(message.author.id)
        logging.info(f"User ID: {message.author.id}, Timezone: {user_tz}")

        # Получаем локальное время пользователя на основе часового пояса
        local_time = datetime.fromtimestamp(timestamp, pytz.timezone(user_tz))
        logging.info(f"Original timestamp: {timestamp}, Local time: {local_time}")

        # Форматируем дату и добавляем " UTC 0"
        return local_time.strftime('%Y-%m-%d %H:%M:%S') + " UTC +0"

    text = re.sub(r'<t:(\d+):[tTdDfFmM]>', format_timestamp, text)

    logging.info(f"Message to be sent: {text}")

    try:
        logging.info("Attempting to send message to Telegram...")
        await telegram_bot.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
        logging.info(f"Sent message to Telegram: {text}")
    except Exception as e:
        logging.error(f"Failed to send message to Telegram: {e}")

    await discord_bot.process_commands(message)


# Обработчик команды для Telegram
async def set_timezone_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    timezone = context.args[0] if context.args else None

    if timezone:
        try:
            # Проверка на валидный часовой пояс
            pytz.timezone(timezone)
            user_timezones[user_id] = timezone
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"Ваш часовой пояс установлен на: {timezone}")
        except pytz.UnknownTimeZoneError:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Неверный часовой пояс. Пожалуйста, введите правильный.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, укажите часовой пояс.")


# Настройка Telegram-бота
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler('set_timezone', set_timezone_telegram))


# Запуск Telegram-бота
async def run_telegram_bot():
    await application.initialize()
    await application.start_polling()


# Запуск Discord-бота
if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()

    # Создание единого Telegram бота
    telegram_bot = application

    loop.create_task(run_telegram_bot())
    loop.run_until_complete(discord_bot.start(DISCORD_TOKEN))
