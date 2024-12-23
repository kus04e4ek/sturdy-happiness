from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import asyncio
import os

import weather

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# В этой переменной будет храниться токен.
# Сделай так, чтобы в переменной API_TOKEN была строка
# с твоим токеном. Помни, что токен - это чувствительная
# информация, и в коде его хранить нельзя.
# Используй чтение из внешнего файла или получи его
# через переменную окружения с помощью os.getenv
API_TOKEN = os.getenv('API_TOKEN')


# Создаём бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

### --- ОБРАБОТЧИК КОМАНД ---
@dp.message(F.text == '/start')
async def start_command(message: types.Message):
    weather.reset(message)
    
    # Создаём кнопки
    button_get_weather = KeyboardButton(text='Получить погоду')

    # Создаём клавиатуру и добавляем кнопки
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_get_weather]],
        resize_keyboard=True
    )

    await message.answer(
        'Привет! Я бот для просмотра погоды, выберите действие с помощью кнопок или отправьте команду /help, чтобы получить все доступные команды',
        reply_markup=reply_keyboard,
    )

@dp.message(F.text == '/help')
async def help_command(message: types.Message):
    weather.reset(message)
    
    await message.answer(
        'Список доступных команд:\n'
        '/start - Начать работу с ботом\n'
        '/help - Получить помощь\n'
        '/weather - Получить прогноз погоды'
    )

@dp.message(F.text.in_(('/weather', 'Получить погоду')))
async def weather_command(message: types.Message):
    await weather.weather_command(message)

### --- CALLBACK-ЗАПРОСЫ ---
@dp.callback_query(F.data.in_(weather.callback))
async def weather_callback(callback: types.CallbackQuery):
    await weather.handle_callbacks(start_command, callback)

### --- НЕОБРАБОТАННЫЕ СООБЩЕНИЯ ---
@dp.message()
async def handle_unrecognized_message(message: types.Message):
    if not await weather.handle_unrecognized_message(message):
        await message.answer('Извините, я не понял ваш запрос. Попробуйте использовать команды или кнопки.')

### --- ЗАПУСК БОТА ---
if __name__ == '__main__':
    async def main():
        # Запускаем polling
        await dp.start_polling(bot)

    asyncio.run(main())
