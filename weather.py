from aiogram import types
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from text_interactions import TextInteractions

import api


# Уникальные переменные для каждого чата.
class ChatValues:
    def __init__(self):
        self.text_interactions = TextInteractions()
        self.city_count = 0
        self.cities = []
        
        self.graph_type = 'Температура'
        self.days = '3'
        self.data = {}

chat_values: dict[int, ChatValues] = {}

# Получить количество дней.
def reset(message: types.Message):
    if message.chat.id in chat_values:
        del chat_values[message.chat.id]

# Сообщение при ошибке.
async def error_message(text, message: types.Message):
    button_return = InlineKeyboardButton(
        text='Вернуться', 
        callback_data='Вернуться'
    )

    # Создаём инлайн-клавиатуру
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_return]]
    )

    await message.answer(text, reply_markup=inline_keyboard)

# Команда /weather.
async def weather_command(message: types.Message):
    chat_values[message.chat.id] = ChatValues()
    
    await chat_values[message.chat.id].text_interactions.set_call_interaction('get_city_count', False, get_city_count, message=message)

# Получить количество городов от пользователя.
async def get_city_count(is_getting_city_count: bool, message: types.Message):
    async def start_message():
        await message.answer(
            'Введите количество городов (минимум 2):',
            reply_markup=ReplyKeyboardRemove()
        )
    
    
    if not is_getting_city_count:
        await start_message()
        return True
    
    try:
        city_count = int(message.text)
    except ValueError:
        await message.answer('Не число.')
        await start_message()
        return True

    if city_count < 2:
        await message.answer('Городов меньше двух.')
        await start_message()
        return True
    
    chat_values[message.chat.id].city_count = city_count
    await chat_values[message.chat.id].text_interactions.set_call_interaction('get_city', 0, get_city, message=message)
    
    return False

# Получить город от пользователя.
async def get_city(count: int, message: types.Message):
    if count == 0:
        count = 1
    else:
        if message.text == '':
            await message.answer('Сообщение пустое.')
        else:
            chat_values[message.chat.id].cities.append(message.text)
            count += 1

    if count > chat_values[message.chat.id].city_count:
        await request_data(message)
        return 0

    if count == 1:
        await message.answer('Начальная точка:')
    elif count == chat_values[message.chat.id].city_count:
        await message.answer('Конечная точка:')
    else:
        await message.answer(f'Промежуточная точка {count - 1}:')
    
    return count

# Запрашивает данные с сервера.
async def request_data(message: types.Message):
    try:
        chat_values[message.chat.id].data = api.get_data(chat_values[message.chat.id].cities)
    except Exception as exception:
        await error_message(str(exception), message)
        return
    
    await show_current_weather(message)
    await show_graph(message)

# Показывает текущую погоду.
async def show_current_weather(message: types.Message):
    def get_title(idx):
        if idx == 0:
            return 'Начальная точка'
        elif idx == chat_values[message.chat.id].city_count - 1:
            return 'Конечная точка'
        else:
            return f'Промежуточная точка {idx}'
    
    await message.answer(
        '\n\n'.join(
            f'*{get_title(idx)}: {i["city_name"]}*\n'
            f'Температура: {i["current"]["temperature"]}\n'
            f'Влажность: {i["current"]["humidity"]}\n'
            f'Скорость ветра: {i["current"]["wind_speed"]}\n'
            f'Вероятность дождя: {i["current"]["rain_probability"]}'
            for idx, i in enumerate(chat_values[message.chat.id].data['cities'])
        ), parse_mode='Markdown'
    )

# Показывает грфик.
async def show_graph(message: types.Message):
    # Создаём инлайн-кнопки
    button_days = InlineKeyboardButton(
        text='3 дня' if chat_values[message.chat.id].days != '3' else '5 дней', 
        callback_data='3' if chat_values[message.chat.id].days != '3' else '5'
    )
    
    button_temperature = InlineKeyboardButton(
        text='График температуры', 
        callback_data='Температура'
    )
    button_humidity = InlineKeyboardButton(
        text='График влажность', 
        callback_data='Влажность'
    )
    button_wind_speed = InlineKeyboardButton(
        text='График скорости ветра', 
        callback_data='Скорость_ветра'
    )
    button_rain_probability = InlineKeyboardButton(
        text='График вероятности дождя', 
        callback_data='Вероятность_дождя'
    )
    graph_buttons = list(filter(
        lambda x: x.callback_data != chat_values[message.chat.id].graph_type,
        (button_temperature, button_humidity, button_wind_speed, button_rain_probability)
    ))
    
    button_return = InlineKeyboardButton(
        text='Вернуться', 
        callback_data='Вернуться'
    )

    # Создаём инлайн-клавиатуру
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_days], graph_buttons[:2], [graph_buttons[2]], [button_return]]
    )
    
    try:
        content = api.get_graph(chat_values[message.chat.id].data['graphs'][chat_values[message.chat.id].graph_type][chat_values[message.chat.id].days])
    except Exception as exception:
        await error_message(str(exception), message)
        return
    
    await message.answer_photo(
        types.BufferedInputFile(content, 'graph.jpg'),
        caption=f'[Ссылка]({chat_values[message.chat.id].data['graphs'][chat_values[message.chat.id].graph_type][chat_values[message.chat.id].days]})',
        parse_mode='Markdown',
        reply_markup=inline_keyboard
    )

# Нажаты инлайн-кнопки.
async def handle_callbacks(start_message, callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    
    if callback.data == 'Вернуться':
        await start_message(callback.message)
        return
    
    if callback.data in ['3', '5']:
        chat_values[callback.message.chat.id].days = callback.data
    else:
        chat_values[callback.message.chat.id].graph_type = callback.data
    
    await show_graph(callback.message)

# Пользователем введён текст.
async def handle_unrecognized_message(message: types.Message):
    if message.chat.id in chat_values:
        return await chat_values[message.chat.id].text_interactions.call_interactions(message=message)
    return False


callback = [
    '3', '5',
    'Температура', 'Влажность', 'Скорость_ветра', 'Вероятность_дождя',
    'Вернуться'
]
