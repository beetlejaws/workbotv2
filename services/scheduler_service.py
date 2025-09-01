import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from nats.js import JetStreamContext
from services.nats_service.publisher import call_publisher
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from db.requests import Database
from db.views import StudentUser
from services.google_services import GoogleDrive
from datetime import datetime, timedelta
import pytz


logger = logging.getLogger(__name__)

async def prepare_and_send_info_for_student(js: JetStreamContext, subject: str, db: Database, telegram_id: int, gd: GoogleDrive, tomorrow: datetime.date, mode: str) -> bool:
    student:  StudentUser = await db.get_student_by_telegram_id(telegram_id)
    if mode == 'lesson':
        data = await db.get_lessons_by_period(student.subject_ids, tomorrow, tomorrow)
        first_string = 'Привет! На завтра запланированы следующие занятия:\n\n'
        last_string = '\n\nТакже не забудь порешать ДЗ с предыдущего занятия:\n\n'
    else:
        today = tomorrow - timedelta(days=1)
        data = await db.get_active_tests(student.class_id, today, tomorrow)
        first_string = 'Привет! В ближайшее время у тебя назначены следующие дедлайны:\n\n'

    if not data:
        return False

    if mode == 'lesson':
        tasks = [gd.process_lesson_html_view(lesson) for lesson in data]
        lessons = await asyncio.gather(*tasks)

        far_far_day = tomorrow - timedelta(days = 14)
        today = tomorrow - timedelta(days = 1)
        unique_subject_ids = set([lesson.id for lesson in data])
        homework_tasks = [db.get_lessons_by_period([subject_id], far_far_day, today) for subject_id in unique_subject_ids]
        homework_data = await asyncio.gather(*homework_tasks)
        homeworks = [x[-1] for x in homework_data]
        homeworks_strings = [await gd.process_homework_html_view(homework) for homework in homeworks]
        message = first_string + '\n\n'.join(lessons) + last_string + '\n\n'.join(homeworks_strings)
    else:
        strings = [gd.process_test_html_view(test) for test in data]
        message = first_string + '\n\n'.join(strings)

    await call_publisher(
        js=js,
        chat_id=student.telegram_id,
        message=message,
        subject=subject
    )

    return True

async def lessons_notification(js: JetStreamContext, session_maker: async_sessionmaker[AsyncSession], gd: GoogleDrive, subject: str):
    async with session_maker() as session:

        db = Database(session)

        telegram_ids = await db.get_sub_lesson_students('lesson')

        logger.info(f'NATS: Запущена рассылка для {len(telegram_ids)} студентов')

        tomorrow = datetime.now().date() + timedelta(days=1)

        tasks = [prepare_and_send_info_for_student(
            js, subject, db, telegram_id, gd, tomorrow, 'lesson'
        ) for telegram_id in telegram_ids]

        await asyncio.gather(*tasks)

async def deadlines_notification(js: JetStreamContext, session_maker: async_sessionmaker[AsyncSession], gd: GoogleDrive, subject: str):
    async with session_maker() as session:

        db = Database(session)

        telegram_ids = await db.get_sub_lesson_students('deadline')

        tomorrow = datetime.now().date() + timedelta(days=1)

        tasks = [prepare_and_send_info_for_student(
            js, subject, db, telegram_id, gd, tomorrow, 'deadline'
        ) for telegram_id in telegram_ids]

        await asyncio.gather(*tasks)

def setup_scheduler(js: JetStreamContext, subject: str, session_maker: async_sessionmaker[AsyncSession], gd: GoogleDrive):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))

    scheduler.add_job(
        lessons_notification,
        CronTrigger(hour=16, minute=0),
        seconds=71,
        args=[js, session_maker, gd, subject]
    )

    scheduler.add_job(
        deadlines_notification,
        CronTrigger(hour=12, minute=0),
        seconds = 47,
        args=[js, session_maker, gd, subject]
    )

    scheduler.start()