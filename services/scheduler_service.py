from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nats.js import JetStreamContext
from services.nats_service.publisher import call_publisher
import asyncio

async def tick(js: JetStreamContext, ids: list, subject: str):
    tasks = [
        call_publisher(
            js=js,
            chat_id=id,
            message='Привет',
            subject=subject
        ) for id in ids
    ]
        

    await asyncio.gather(*tasks)

def setup_scheduler(js, ids, subject):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        tick,
        'interval',
        seconds=30,
        args=[js, ids, subject]
    )

    scheduler.start()