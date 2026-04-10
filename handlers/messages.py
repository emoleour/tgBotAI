
import aiohttp
import logging
import os




from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from ollama import Client
from database.database import add_user, get_user, save_message, get_message
from rag.rag import rag
from config.config import Config, load_config

#Этот модуль предназначен только для ИИ
#В стадии разработки полноценного rag и полной работы с chromadb


#Инициализируем роутер
router = Router()

#Инициализируем логгер

logger = logging.getLogger(__name__)


#for Ollama

OLLAMA_GENERATE_URL = 'https://ollama.com/api/generate'
MODEL_NAME = 'deepseek-v3.1:671b'
config: Config = load_config()
OLLAMA_API_KEY = config.ollama_token.api_token

#Системный промт

SYSTEM_PROMPT = ('Твое имя - Электрик. \n'
                'Ты - полезный ассистент, который отвечает на вопросы '
                'используя предоставленные примеры.\n'
                'Главное - ты электромонтажник и не знаешь ответа на вопросы о погоде и тому подобное.\n'
                'А также ты не выполняешь задания связанные с написаем программного кода.')

async def query_ollama(prompt: str) -> str:

    logger.debug('Промт для Ollama:\n%s', prompt)

    headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user",  "content": prompt}],
        "stream": False,

    }
    try:
        async with aiohttp.ClientSession(trust_env=False) as session:
            async with session.post('https://ollama.com/v1/chat/completions', json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data['choices'][0]['message']['content'].strip()
                    if not content:
                        logger.warning('Модель вернула пустой ответ')
                        return 'Модель не дала ответ :('
                    return content
                else:
                    text = await resp.text()
                    logger.error("Ollama вернул статус %d, тело: %s", resp.status, text)
                    return f"Извините, ошибка при обращении к модели (статус {resp.status})."
    except Exception as e:
        logger.exception(f"Ошибка при запросе к Ollama {e}")
        return "Не удалось получить ответ от модели."




@router.message()
async def handle_message(message: Message):
    user = message.from_user
    user_id = user.id
    user_question = message.text.strip()
    if not user_question:
        return

    await add_user(user_id, user.username, user.first_name, user.last_name)
    await save_message(user_id, 'user', user_question)
    history = await get_message(user_id, limit=5)

    history_text = ''
    for msg in history:
        role = 'Пользователь' if msg['role'] == 'user' else 'Ассистент'
        history_text += f'{role}: {msg["content"]}\n'

    #Ищем похожие примеры в БД
    examples = await rag.find_relevant_examples(user_question, n_results=3)


    #формируем промт
    prompt_parts = [SYSTEM_PROMPT]
    if history_text:
        prompt_parts.append("История диалога:\n" + history_text)
    if examples:
        example_text = ''
        for ex in examples:
            example_text += f"Вопрос: {ex['question']}\nОтвет: {ex['answer']}\n\n"
        prompt_parts.append("Вот несколько примеров:\n" + example_text)
    prompt_parts.append(f"Вопрос: {user_question}\nОтвет:")

    prompt = '\n\n'.join(prompt_parts)

    # 7. Получаем ответ от модели
    answer = await query_ollama(prompt)

    # 8. Сохраняем ответ ассистента
    await save_message(user_id, 'assistant', answer)

    # 9. Отправляем пользователю
    await message.answer(answer)






