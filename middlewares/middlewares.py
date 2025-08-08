from typing import Any, Awaitable, Callable, Dict
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from db.requests import Database


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session: async_sessionmaker[AsyncSession]) -> None:
        self.session = session

    async def __call__(
        self, 
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject, 
        data: Dict[str, Any]) -> Any:

        async with self.session() as session:
            db = Database(session=session)
            data['db'] = db
            return await handler(event, data)
        
class UserMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:
                
        db: Database = data['db']

        telegram_id = data['event_from_user'].id

        data['telegram_id'] = telegram_id
        try:
            data['student_id'] = await db.get_student_id(telegram_id)
            data['class_id'] = await db.get_student_class_id(telegram_id)
            data['variant'] = await db.get_student_variant(telegram_id)
        except:
            return await handler(event, data)
        
        return await handler(event, data)