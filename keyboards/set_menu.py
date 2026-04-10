from aiogram import Bot
from aiogram.types import BotCommand

async def set_main_menu(bot: Bot):
    main_menu_command = [
        BotCommand(command='/help', description='Описание работы бота'),
        BotCommand(command='/support', description='Задать вопрос о работе бота?'),
        BotCommand(command='/menu', description='В разработке...'),
        BotCommand(command='/start', description='Перезапуск бота'),

    ]
    await bot.set_my_commands(main_menu_command)
