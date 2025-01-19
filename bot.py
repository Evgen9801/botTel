# -*- coding: utf-8 -*-

import logging
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
import re

# Включаем логирование для отладки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ключ Yandex API
YANDEX_API_KEY = "your_api_key_here"  # Вставьте ваш правильный API-ключ

# URL Yandex API
YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Заголовки для запросов
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Api-Key AQVN2S2-LNaAPFiOaj6hXOgkNacGnbJGYls0My6L",  # Правильный API-ключ
}

# Настройки модели
MODEL_CONFIG = {
    "modelUri": "gpt://b1gh89822qbjtjq5mm30/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": 2000
    },
    "messages": [
        {
            "role": "system",
            "text": "Ты — помощник, отвечай на все вопросы, которые тебе задают, на основе полученной информации."
        }
    ]
}

# Словарь для хранения истории сообщений и состояния игры
user_conversations = {}

# База данных с информацией о произведениях и анализах
books_data = {
    "белые ночи": {
        "summary": "Роман Ф.М. Достоевского, рассказывающий о встрече героя с женщиной, которая ему привиделась в его снах, и о том, как эта встреча изменяет его жизнь.",
        "analysis": {
            "призрак": {
                "summary": "Мотив призрачности в повести «Белые ночи» связан с внутренними переживаниями героя. Встречи и мечты героя часто оказываются эфемерными, как призраки, исчезающие при свете реальности.",
                "details": [
                    "Слово 'призрак' символизирует иллюзорность жизни героя и пустоту его мечт.",
                    "Главный герой, сравнивая свою жизнь с призраком, отражает внутреннее одиночество и эфемерность своих надежд.",
                    "В момент встречи с Настенькой слово 'призрак' подчеркивает хрупкость и нереальность его счастья."
                ],
                "quotes": [
                    "Моя жизнь — как призрак, несущийся над пустынной землёй.",
                    "Она была для меня как призрак, неосязаемая, словно сон."
                ],
                "answers": {
                    "анализ мотивов призрачности": "Мотив призрачности в повести проявляется через внутреннее одиночество главного героя, который воспринимает свою жизнь как нечто эфемерное и неосязаемое. Это отражается как в его переживаниях, так и в его отношении к Настеньке, что символизирует обманчивость мечт."
                }
            }
        }
    }
}

# Функция для ответа на вопросы с анализом
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.strip()  # Получаем сообщение от пользователя
    user_id = update.message.from_user.id  # Получаем ID пользователя для хранения истории

    # Логируем сообщение, которое прислал пользователь
    logger.info(f"Пользователь {update.message.from_user.username} ({user_id}) написал: {user_text}")

    # Проверка на фразы типа "Знаешь chat gpt?"
    if "Знаешь chat gpt?" in user_text.lower():
        await update.message.reply_text("Конечно, я знаю! ChatGPT - это очень умный ИИ, который может помочь тебе с чем угодно!")
        return

    # Добавляем текущее сообщение пользователя в историю
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({"role": "user", "text": user_text})

    # Если пользователь спрашивает про мотивацию призрачности
    if "призрак" in user_text.lower() and "белые ночи" in user_text.lower():
        book_info = books_data.get("белые ночи")
        if book_info and "призрак" in book_info["analysis"]:
            analysis = book_info["analysis"]["призрак"]
            response = f"Мотив призрачности в повести 'Белые ночи':\n\n"
            response += f"{analysis['summary']}\n\n"
            response += "Ключевые моменты анализа:\n"
            for detail in analysis["details"]:
                response += f"- {detail}\n"
            response += "\nЦитаты:\n"
            for quote in analysis["quotes"]:
                response += f"• {quote}\n"
            # Проверка на детализированный запрос
            if "анализ мотивов призрачности" in user_text.lower():
                response += "\nПодробный анализ:\n"
                response += analysis["answers"]["анализ мотивов призрачности"]
        else:
            response = "Не удалось найти информацию о мотивации призрачности в произведении."
        await update.message.reply_text(response)
        return

    # Создаем запрос для Yandex API
    model_request = MODEL_CONFIG.copy()
    model_request["messages"].extend(user_conversations[user_id])

    try:
        # Используем aiohttp для асинхронного запроса
        async with aiohttp.ClientSession() as session:
            async with session.post(YANDEX_API_URL, json=model_request, headers=HEADERS) as response:
                response.raise_for_status()  # Проверяем успешность запроса

                # Разбираем JSON-ответ
                result = await response.json()
                logger.info(f"Ответ от Yandex API: {result}")  # Логируем ответ для отладки

                # Извлекаем текст ответа
                reply_text = (
                    result.get("result", {})
                    .get("alternatives", [{}])[0]
                    .get("message", {})
                    .get("text", "Не удалось получить текст ответа.")
                )

                # Логируем, что бот собирается отправить
                logger.info(f"Ответ бота: {reply_text}")

                # Отправляем ответ пользователю
                await update.message.reply_text(reply_text)

    except Exception as e:
        response = f"Ошибка: {str(e)} 😞"
        logger.error(f"Ошибка запроса к Yandex API: {str(e)}")
        await update.message.reply_text(response)

# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Привет! Я Алиса. Могу поговорить на любую тему или ответить на вопросы! Что тебя интересует?")

# Основная функция
def main():
    # Токен бота от BotFather
    TELEGRAM_BOT_TOKEN = "8135223868:AAHlHKjkPIrlm6Fv-4qXhQBGX-pEjGmkzew"  # Вставленный токен

    if not TELEGRAM_BOT_TOKEN:
        logger.error("Токен Telegram не указан. Проверьте TELEGRAM_BOT_TOKEN.")
        return

    # Создаем экземпляр Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Бот запущен. Ожидаю сообщений...")
    application.run_polling()

if __name__ == "__main__":
    main()
