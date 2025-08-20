import asyncio
import json
import logging

from aiogram import Bot
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter,
)

from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext


logger = logging.getLogger(__name__)

class SendMessageConsumer:

    def __init__(
            self,
            nc: Client,
            js: JetStreamContext,
            bot: Bot,
            subject: str,
            stream: str,
            durable_name: str
    ) -> None:
        self.nc = nc
        self.js = js
        self.bot = bot
        self.subject = subject
        self.stream = stream
        self.durable_name = durable_name

        self.is_running = False

    async def start(self):
        self.stream_sub = await self.js.pull_subscribe(
            subject=self.subject,
            stream=self.stream,
            durable=self.durable_name
        )

        self.is_running = True

        logger.info('Consumer NATS запущен')

        await self.process_messages()

    async def process_messages(self) -> None:
        
        while self.is_running:
            try:
                messages = await self.stream_sub.fetch(batch=25)
                if not messages:
                    continue

                logger.info(f"Получен батч из {len(messages)} сообщений")

                tasks = []
                for msg in messages:
                    task = asyncio.create_task(self.process_message(msg))
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info('Сообщения отправлены')

            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Ошибка обработки батча: {e}")

    async def process_message(self, msg: Msg) -> None:
        try:
            data = json.loads(msg.data.decode())
            chat_id = data['chat_id']
            message = data['message']

            await self.send_message(chat_id, message)

            await msg.ack()

        except TelegramRetryAfter as e:
            logger.warning(f" Rate limit, сообщение будет обработано позже: {e}")

        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await msg.ack()

    async def send_message(self, chat_id: str | int, message: str):
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="HTML"
            )
        
        except TelegramRetryAfter as e:
            logger.warning(
                f"Rate limit для пользователя {chat_id}: повтор через {e.retry_after} сек"
            )
            raise

        except TelegramNotFound:
            logger.warning(f"Пользователь {chat_id} не найден")
        
        except TelegramForbiddenError:
            logger.warning(f"Пользователь {chat_id} заблокировал бота")