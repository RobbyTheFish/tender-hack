import logging
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import Throttled

import requests

from .bot import dp, bot
from .states import Form
from .config import Config

logger = logging.getLogger(__name__)

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Я помогу вам сгенерировать отчет. "
        "Пожалуйста, отправьте URL(ы) для проверки. "
        "Вы можете отправить один URL или несколько, разделенных запятой."
    )
    await Form.waiting_for_urls.set()

# Команда /help
@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_text = (
        "Этот бот помогает генерировать отчеты по указанным URL.\n\n"
        "Команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/help - Получить справку\n\n"
        "Инструкция:\n"
        "1. Отправьте один или несколько URL, разделенных запятой.\n"
        "2. Выберите критерии оценки для проверки.\n"
        "3. Получите PDF-отчет."
    )
    await message.answer(help_text)

# Обработка полученных URL
@dp.message_handler(state=Form.waiting_for_urls)
async def process_urls(message: types.Message, state: FSMContext):
    urls = [url.strip() for url in message.text.split(",") if url.strip()]
    if not urls:
        await message.answer("Пожалуйста, отправьте корректные URL(ы).")
        return
    await state.update_data(urls=urls)
    
    # Создание клавиатуры для выбора критериев
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = [
        KeyboardButton("1"),
        KeyboardButton("2"),
        KeyboardButton("3"),
        KeyboardButton("4"),
        KeyboardButton("5"),
        KeyboardButton("6"),
        KeyboardButton("Все")
    ]
    keyboard.add(*buttons)
    await message.answer(
        "Выберите критерии оценки (можно выбрать несколько, разделяя пробелами, "
        "или отправьте 'Все' для выбора всех критериев):",
        reply_markup=keyboard
    )
    await Form.waiting_for_criteria.set()

# Обработка выбранных критериев
@dp.message_handler(state=Form.waiting_for_criteria)
async def process_criteria(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    urls = user_data.get('urls', [])
    
    criteria_input = message.text.strip().lower()
    if criteria_input == "все":
        criteria = [1, 2, 3, 4, 5, 6]
    else:
        try:
            criteria = list(map(int, criteria_input.replace(',', ' ').split()))
            # Проверка корректности критериев
            if not all(1 <= c <= 6 for c in criteria):
                raise ValueError
        except ValueError:
            await message.answer("Пожалуйста, выберите критерии от 1 до 6 или отправьте 'Все'.")
            return
    
    # Подготовка данных для API запроса
    payload = {
        "urls": urls,
        "criteria": criteria
    }
    
    await message.answer("Генерирую отчет, пожалуйста, подождите...", reply_markup=ReplyKeyboardRemove())
    
    try:
        response = requests.post(Config.API_URL, json=payload)
        response.raise_for_status()
        pdf_content = response.content
        
        # Отправка PDF пользователю
        await bot.send_document(
            chat_id=message.chat.id,
            document=pdf_content,
            filename="report.pdf"
        )
        await message.answer("Отчет успешно сгенерирован и отправлен.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await message.answer("Произошла ошибка при генерации отчета. Пожалуйста, попробуйте позже.")
    
    await state.finish()

# Обработка других сообщений
@dp.message_handler()
async def default_handler(message: types.Message):
    await message.answer("Я не понимаю эту команду. Введите /help для получения справки.")
