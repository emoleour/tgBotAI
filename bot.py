import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config.config import Config, load_config

from database.database import init_db
from handlers import messages
from rag.rag import rag
from keyboards.set_menu import set_main_menu
from keyboards.other import other_router


#Инициализируем логгер

logger = logging.getLogger(__name__)




#action for startup bot
async def on_startup():

    await init_db()
    await rag.load_example_from_file('examples.json')


#Функция конфигурирования и запуска

async def main():

    config: Config = load_config()

    #Задаем конфигурацию логирования
    logging.basicConfig(level=logging.getLevelName(level=config.log.level),
                        format=config.log.format
                        )

    #Для информации о запуске
    logger.info('Бот запущен')

    #Инициализируем бот и диспетчер
    bot = Bot(token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    #init main menu
    await set_main_menu(bot)

    # init db
    db = init_db()

    #Сохраняем БД в workflow data
    dp.workflow_data.update(db=db)

    #Регистрируем роутеры в диспетчере
    dp.include_router(other_router)
    dp.include_router(messages.router)


    #Регистрируем функцию on_startup
    dp.startup.register(on_startup)


    #Пропускаем накопившиеся апдейты и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())





