from datetime import date
import asyncio
from utils.utils import *

from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format, List
from aiogram_dialog.widgets.kbd import Button, Radio, ManagedRadio, Cancel

from db.requests import Database
from db.views import StudentUser
from services.google_services import GoogleDrive

from dialogs.states import ScheduleSG


#handlers
async def month_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['current_month'] = int(item_id)

async def course_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_course'] = int(item_id)

#getters
async def schedule_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, first_workday: date, last_workday: date, **kwargs):
    if dialog_manager.dialog_data.get('current_month') is None:
        current_month = dialog_manager.dialog_data['current_month'] = date.today().month
        radio_month: ManagedRadio = dialog_manager.find('month') # type: ignore
        await radio_month.set_checked(current_month)
    else:
        current_month = dialog_manager.dialog_data['current_month']

    months = {1: 'ЯНВ', 2: 'ФЕВ', 3: 'МАР', 4: 'АПР',
              5: 'МАЙ', 6: 'ИЮН', 7: 'ИЮЛ', 8: 'АВГ',
              9: 'СЕН', 10: 'ОКТ', 11: 'НОЯ', 12: 'ДЕК'}
    first_month = first_workday.month
    last_month = last_workday.month
    months_names = [(months[i], i) for i in range(first_month, last_month + 1)]

    
    courses_data = await db.get_courses_for_class(student.class_id)
    if dialog_manager.dialog_data.get('chosen_course') is None:
        radio_course: ManagedRadio = dialog_manager.find('chosen_course') # type: ignore
        chosen_course = courses_data[0][1]
        dialog_manager.dialog_data['chosen_course'] = chosen_course
        await radio_course.set_checked(chosen_course)
    else:
        chosen_course = dialog_manager.dialog_data['chosen_course']

    lessons_info = []
    
    folder_id = await db.get_folder_id_by_object(chosen_course)


    start_date = get_first_day_of_month(current_month)
    end_date = get_last_day_of_month(current_month)
    lessons_data = await db.get_lessons_by_period([chosen_course], start_date, end_date)

    async def process_lesson(lesson: dict) -> str:
        number = lesson['number']
        file_name = (f'Занятие {number}' if number > 9 else f'Занятие 0{number}') + '.pdf'
        file_id = await gd.get_file_id_by_name(file_name, folder_id)  # type: ignore
        
        if file_id is not None:
            file_link = await gd.get_file_link(file_id)
            return f'<a href="{file_link}">{combine_lesson_info(lesson)}</a>'
        return combine_lesson_info(lesson)
        
    tasks = [process_lesson(lesson) for lesson in lessons_data]
    lessons_info = await asyncio.gather(*tasks)
    
    return {'lessons_info': lessons_info,
            'months_names': months_names,
            'courses': courses_data
    }

schedule_dialog = Dialog(
    Window(
        List(
            field=Format('{item}'),
            items='lessons_info',
            sep='\n\n'
        ),
        Radio(
            checked_text=Format('🔘 {item[0]}'),
            unchecked_text=Format('{item[0]}'),
            id='month',
            item_id_getter=lambda x: x[1],
            items='months_names',
            on_state_changed=month_selection # type: ignore
        ),
        Radio(
            checked_text=Format('🔘 {item[0]}'),
            unchecked_text=Format('{item[0]}'),
            id='chosen_course',
            item_id_getter=lambda x: x[1],
            items='courses',
            on_state_changed=course_selection # type: ignore
        ),
        Cancel(
            text=Const('⬅️ Назад'),
        ),
        parse_mode='HTML',
        state=ScheduleSG.show,
        getter=schedule_getter
    )
)