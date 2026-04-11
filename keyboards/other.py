import logging

from aiogram import Router, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from rag.rag import rag

from database.database import add_user, get_user, save_message, get_message


#Инциализируем Router
other_router = Router()

#Инициализируем логгер
logger = logging.getLogger(__name__)

@other_router.message(CommandStart())
async def command_start(message: Message):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name, user.last_name)
    await message.answer(text=f'Привет, {message.from_user.first_name}! Это персональный помощник для людей, которые\n'
                              f'не знают и не разбираются в электромонтаже. \n'
                              f'Напиши в чат любой вопрос про электромонтаж и помощник тебе ответит.')



@other_router.message(Command(commands='help'))
async def command_help(message: Message):
    await message.answer(text=f'Этот бот не требует регистрации.\n'
                              f'Доступные команды для бота в разработке.\n'
                              f'По вопросам сотрудничества и предложений прошу обращаться: emoleour.mu@gmail.com'
                         )

@other_router.message(Command(commands='support'))
async def command_support(message: Message):
    await message.answer(text=f'1. Если бот не отвечает. - Возможно он не хочет :).\n'
                              f'2. По остальным вопросам связанным с техподдержкой обращаться: emoleour.mu@gmail.com')


# для теста, возвращает ли модель ответы
@other_router.message(Command(commands='test'))
async def test_rag(message: Message):
    user_question = 'Какой твой любимый цвет?'
    examples = await rag.find_relevant_examples(user_question,n_results=3)
    await message.answer(text=f'Найдено примеров: {len(examples)}\n{examples}')

@other_router.message(Command(commands='menu'))
async def command_menu(message: Message):
    await message.answer(text='f В Разработке...')