import logging
import asyncio
from aiogram import Bot


class TgFilter(logging.Filter):
    def filter(self, record):
        return 'NATS' in record.msg.upper() or 'STUDENT' in record.msg.upper()

class ToFileFilter(logging.Filter):
    def filter(self, record):
        return 'FILE' in record.msg.upper()
    
class NotToFileFilter(logging.Filter):
    def filter(self, record):
        return 'FILE' not in record.msg.upper()

class TgLogsHandler(logging.Handler):
    def __init__(self, bot: Bot, chat_id: int, topic_id: int):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id
        self.topic_id = topic_id

    def emit(self, record):
        log_entry = self.format(record)

        asyncio.create_task(self._send_async(log_entry))
        
    async def _send_async(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=self.topic_id,
                text=message
            )
        except:
            pass

def tg_logs_handler_factory(bot: Bot, chat_id: int, topic_id: int):
    return TgLogsHandler(bot, chat_id, topic_id)

def setup_logging(bot: Bot, chat_id: int, info_topic_id: int, error_topic_id: int):
    tg_info_handler = tg_logs_handler_factory(bot, chat_id, info_topic_id)
    tg_info_handler.setLevel(logging.INFO)
    tg_info_handler.addFilter(TgFilter())

    tg_error_handler = tg_logs_handler_factory(bot, chat_id, error_topic_id)
    tg_error_handler.setLevel(logging.WARNING)
    tg_error_handler.addFilter(NotToFileFilter())

    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    file_handler.setLevel(logging.WARNING)
    file_handler.addFilter(ToFileFilter())

    logging.basicConfig(
        level=logging.INFO,
        format='#%(levelname)-8s [%(asctime)s] - %(message)s',
        handlers=[
            file_handler,
            tg_info_handler,
            tg_error_handler
        ]
    )