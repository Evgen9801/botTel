from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

# Ключ Yandex API
YANDEX_API_KEY = "AQVN1pLvbj8Q-ALeZLZOwcc5zXYMvtIk9WhdxYk7"

# URL Yandex API
YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# Настройки для запросов к Yandex API
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {YANDEX_API_KEY}",
}

# Конфигурация модели
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
            "text": "Найди ошибки в тексте и исправь их"
        }
    ]
}

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Отправь мне текст, и я проверю его на ошибки.")

# Обработчик сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text

    # Добавляем сообщение пользователя в запрос
    model_request = MODEL_CONFIG.copy()
    model_request["messages"].append({"role": "user", "text": user_text})

    try:
        # Отправляем запрос в Yandex API
        response = requests.post(YANDEX_API_URL, json=model_request, headers=HEADERS)
        response.raise_for_status()  # Проверяем, успешен ли запрос

        # Получаем результат
        result = response.json()
        reply_text = result.get("result", {}).get("text", "Не удалось получить ответ.")
    except Exception as e:
        reply_text = f"Ошибка: {str(e)}"

    # Отправляем ответ пользователю
    update.message.reply_text(reply_text)

# Основная функция
def main():
    # Вставьте токен вашего бота от BotFather
    TELEGRAM_BOT_TOKEN = "8135223868:AAHlHKjkPIrlm6Fv-4qXhQBGX-pEjGmkzew"

    # Создаем экземпляр Updater
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Регистрируем обработчики
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if name == "__main__":
    main()