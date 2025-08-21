from config import load_config
import logging
import asyncio
from aiogram import Bot, Dispatcher
from dialogs.setup import setup_my_dialogs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from middlewares.middlewares import DatabaseMiddleware, UserMiddleware
import start_handler
from services.google_services import GoogleSheets, GoogleDrive
from services.nats_service import nats_connect
from services.scheduler_service import setup_scheduler
from services.nats_service.storage import NatsStorage

async def main():

    config = load_config()
    engine = create_async_engine(url=config.db.url)

    sessionmaker = async_sessionmaker(engine)

    bot = Bot(token=config.bot.token)
    gs = GoogleSheets(config.google_service.credentials_path)
    gd = GoogleDrive(config.google_service.credentials_path)
    sheets_ids: dict = config.google_service.sheets_ids
    
    nc, js = await nats_connect.connect_to_nats(config.nats.servers)
    await nats_connect.create_stream(
        js=js,
        subject=config.consumer.subject,
        stream=config.consumer.stream
    )

    storage: NatsStorage = await NatsStorage(
        nc=nc,
        js=js
    ).create_storage()

    dp = Dispatcher(storage=storage)

    ids = ['7973947155'] * 2
    setup_scheduler(js, ids, config.consumer.subject)
    
    dp.workflow_data.update(
        {'gs': gs,
         'gd': gd,
         'sheets_ids': sheets_ids,
         'admin_id': config.bot.admin_id,
         'first_workday': config.calendar.first_workday,
         'last_workday': config.calendar.last_workday}
    )

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    dp.include_router(start_handler.router)
    setup_my_dialogs(dp)

    dp.update.outer_middleware(DatabaseMiddleware(session=sessionmaker))
    dp.update.outer_middleware(UserMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await asyncio.gather(
            dp.start_polling(bot),
            nats_connect.start_consumer(
                nc=nc,
                js=js,
                bot=bot,
                subject=config.consumer.subject,
                stream=config.consumer.stream,
                durable_name=config.consumer.durable_name
            )
        )
    except Exception as e:
        logger.error(e)
    finally:
        await nc.close()
        logger.info('Cоединение с NATS закрыто')



if __name__ == '__main__':
    asyncio.run(main())