from config import load_config
import logging
import asyncio
from aiogram import Bot, Dispatcher
from dialogs.setup import setup_my_dialogs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from middlewares.middlewares import DatabaseMiddleware, UserMiddleware
import handlers
from services.google_services import GoogleSheets

async def main():

    config = load_config()
    engine = create_async_engine(url=config.db.url)

    sessionmaker = async_sessionmaker(engine)

    bot = Bot(token=config.bot.token)
    gs = GoogleSheets(config.google_service.credentials_path)
    sheets_ids: dict = config.google_service.sheets_ids

    dp = Dispatcher()
    
    dp.workflow_data.update({'gs': gs, 'sheets_ids': sheets_ids, 'admin_id': config.bot.admin_id})

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    dp.include_router(handlers.router)
    setup_my_dialogs(dp)

    dp.update.outer_middleware(DatabaseMiddleware(session=sessionmaker))
    dp.update.outer_middleware(UserMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())