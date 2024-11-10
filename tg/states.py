from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_urls = State()
    waiting_for_criteria = State()
