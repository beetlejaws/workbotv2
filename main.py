from config import load_config
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message


async def main():

    config = load_config()

    bot = Bot(token=config.bot.token)

    dp = Dispatcher()

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    @dp.message(CommandStart())
    async def start_message(message: Message):
        await message.answer(
            text='OK'
        )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())