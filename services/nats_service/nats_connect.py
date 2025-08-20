import nats
from nats.aio.client import Client
from nats.js import JetStreamContext
from nats.js.api import StreamConfig
from aiogram import Bot
from services.nats_service.consumer import SendMessageConsumer


async def connect_to_nats(servers: list[str]) -> tuple[Client, JetStreamContext]:

    nc: Client = await nats.connect(servers)
    js: JetStreamContext = nc.jetstream()

    return nc, js

async def create_stream(js: JetStreamContext, subject: str, stream: str):

    stream_config = StreamConfig(
        name=stream,
        subjects=[subject],
        retention='limits',
        max_bytes=300 * 1024 * 1024,
        max_msg_size=10 * 1024 * 1024,
        storage='file',
        allow_direct=True,
    )

    await js.add_stream(stream_config)

async def start_consumer(
        nc: Client,
        js: JetStreamContext,
        bot: Bot,
        subject: str,
        stream: str,
        durable_name: str
) -> None:
    
    consumer = SendMessageConsumer(
        nc = nc,
        js=js,
        bot=bot,
        subject=subject,
        stream=stream,
        durable_name=durable_name
    )
    await consumer.start()