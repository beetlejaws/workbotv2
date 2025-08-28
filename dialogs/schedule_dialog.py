from datetime import date
import asyncio
import json
from utils.utils import *

from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format, List
from aiogram_dialog.widgets.kbd import Button, Radio, ManagedRadio, Cancel

from db.requests import Database
from db.views import StudentUser, Subject, Lesson
from services.google_services import GoogleDrive

from dialogs.states import ScheduleSG
from dialogs.utils import radio_check_choice


#handlers
async def month_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_month'] = int(item_id)

async def course_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_subject'] = int(item_id)

#getters
async def schedule_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, first_workday: date, last_workday: date, **kwargs):

    first_month = first_workday.month
    last_month = last_workday.month
    default_month = date.today().month if date.today().month <= last_month else last_month
    current_month = await radio_check_choice(dialog_manager, 'chosen_month', 'chosen_month', default_month)

    months = {1: 'ЯНВ', 2: 'ФЕВ', 3: 'МАР', 4: 'АПР',
              5: 'МАЙ', 6: 'ИЮН', 7: 'ИЮЛ', 8: 'АВГ',
              9: 'СЕН', 10: 'ОКТ', 11: 'НОЯ', 12: 'ДЕК'}
    months_names = [(months[i], i) for i in range(first_month, last_month + 1)]

    if not dialog_manager.dialog_data.get('subjects_list'):
        subjects_list = await db.get_subjects_by_ids(student.subject_ids)
        dialog_manager.dialog_data['subjects_list'] = json.dumps([s.model_dump() for s in subjects_list])
    else:
        subjects_list = [Subject(**s) for s in json.loads(dialog_manager.dialog_data['subjects_list'])]

    subjects_data = [(subject.course_title, index) for index, subject in enumerate(subjects_list)]

    subject_index = await radio_check_choice(dialog_manager, 'chosen_subject', 'chosen_subject', 0)
    subject: Subject = subjects_list[subject_index]

    start_date = get_first_day_of_month(current_month)
    end_date = get_last_day_of_month(current_month)

    lessons_list = await db.get_lessons_by_period([subject.id], start_date, end_date)
        
    tasks = [gd.process_lesson_html_view(lesson) for lesson in lessons_list]
    lessons_info = await asyncio.gather(*tasks)
    
    return {'lessons_info': lessons_info,
            'months_names': months_names,
            'subjects_data': subjects_data
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
            id='chosen_month',
            item_id_getter=lambda x: x[1],
            items='months_names',
            on_state_changed=month_selection # type: ignore
        ),
        Radio(
            checked_text=Format('🔘 {item[0]}'),
            unchecked_text=Format('{item[0]}'),
            id='chosen_subject',
            item_id_getter=lambda x: x[1],
            items='subjects_data',
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