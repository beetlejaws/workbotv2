import asyncio
from datetime import datetime, timedelta
from utils.utils import *

from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format, List, Case
from aiogram_dialog.widgets.kbd import Radio, ManagedRadio, Cancel

from db.requests import Database
from db.views import StudentUser
from services.google_services import GoogleDrive

from dialogs.states import SoonSG


#handlers
async def mode_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['current_mode'] = item_id

async def period_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['current_period'] = item_id

#getters
async def soon_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, **kwargs):

    now = datetime.now()
    now_date = now.date()
    last_day_this_week = get_last_day_of_week(now_date)
    first_day_next_week = last_day_this_week + timedelta(days=1)
    last_day_next_week = first_day_next_week + timedelta(days=7)

    async def get_data(period: str, mode: str):
        periods = {
        'today': (now_date, now_date),
        'this_week': (now_date, last_day_this_week),
        'next_week': (first_day_next_week, last_day_next_week)
        }

        start_date, end_date = periods[period]

        if mode == 'lessons':
            courses_data = await db.get_courses_for_class(student.class_id)
            object_ids = [i[1] for i in courses_data]
            data = await db.get_lessons_by_period(object_ids, start_date, end_date)
        else:
            data = await db.get_active_tests(student.class_id, start_date=start_date, end_date=end_date)

        return data

    async def process_lesson(lesson: dict) -> str:
        number = lesson['number']
        folder_id = await db.get_folder_id_by_object(lesson['id'])
        file_name = (f'Занятие {number}' if number > 9 else f'Занятие 0{number}') + '.pdf'
        file_id = await gd.get_file_id_by_name(file_name, folder_id)  # type: ignore
        
        if file_id is not None:
            file_link = await gd.get_file_link(file_id)
            return f'<a href="{file_link}">{combine_lesson_info(lesson)}</a>'
        return combine_lesson_info(lesson)
    
    def process_test(test: dict) -> str:
        folder_id = test['public_folder_id']
        folder_link = f'https://drive.google.com/drive/folders/{folder_id}'
        return f'<a href="{folder_link}">{combine_test_info(test)}</a>'
    
    if dialog_manager.dialog_data.get('current_period') is None:
        current_period = 'today'
        period_radio: ManagedRadio = dialog_manager.find('period') # type: ignore
        await period_radio.set_checked(current_period)
    else:
        current_period = dialog_manager.dialog_data['current_period']

    if dialog_manager.dialog_data.get('current_mode') is None:
        current_mode = 'lessons'
        mode_radio: ManagedRadio = dialog_manager.find('mode') # type: ignore
        await mode_radio.set_checked(current_mode)
    else:
        current_mode = dialog_manager.dialog_data['current_mode']

    data = await get_data(current_period, current_mode)
    check = False
    info = []

    if len(data) > 0:
        check = True
        if current_mode == 'lessons':
            tasks = [process_lesson(lesson) for lesson in data]
            info = await asyncio.gather(*tasks)
        else:
            info = [process_test(test) for test in data.values()] # type: ignore

    periods = [('Сегодня', 'today'), ('Эта неделя', 'this_week'), ('След. неделя', 'next_week')]
    modes = [('Занятия', 'lessons'), ('Дедлайны', 'deadlines')]

    return {
        'info': info,
        'check': check,
        'periods': periods,
        'modes': modes
    }


soon_dialog = Dialog(
    Window(
        Case(
            texts={
                True: List(
                    field=Format('{item}'),
                    items='info',
                    sep='\n\n',
                ),
                False: Const('За указанный период ничего не найдено'),
            },
            selector='check'
        ),
        Radio(
            checked_text=Format('🔘 {item[0]}'),
            unchecked_text=Format('{item[0]}'),
            id='period',
            item_id_getter=lambda x: x[1],
            items='periods',
            on_state_changed=period_selection # type: ignore
        ),
        Radio(
            checked_text=Format('🔘 {item[0]}'),
            unchecked_text=Format('{item[0]}'),
            id='mode',
            item_id_getter=lambda x: x[1],
            items='modes',
            on_state_changed=mode_selection # type: ignore
        ),
        Cancel(
            text=Const('⬅️ Назад'),
        ),
        state=SoonSG.show,
        getter=soon_getter,
        parse_mode='HTML'
    )
)