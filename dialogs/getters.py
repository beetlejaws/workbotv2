import asyncio
from aiogram.types import User
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import ManagedRadio
from db.requests import Database
from services.google_services import GoogleSheets, GoogleDrive
from datetime import date
from utils.utils import *
from db.views import StudentUser


async def telegram_id_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    event_from_user.username

async def get_sheets_data(dialog_manager: DialogManager, sheets_ids: dict, **kwargs):
    sheets_data = list(sheets_ids.items())
    return {'sheets_data': sheets_data}

async def folder_link_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, **kwargs):
    folder_id = await db.get_class_folder_id(student.class_id)
    folder_link = gd.get_folder_link(folder_id)
    return {'folder_link': folder_link}

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

async def send_work_getter(dialog_manager: DialogManager, db: Database, student: StudentUser, **kwargs):
    tests_data = await db.get_active_tests(student.class_id)
    dialog_manager.dialog_data['tests_data'] = tests_data
    if tests_data is None or not tests_data:
        show_mode = False
        tests = None
    else:
        show_mode = True
        tests = list(map(lambda x: (x, tests_data[x]['course_title'], tests_data[x]['test_title']), tests_data.keys()))

    return {
        'show_mode': show_mode,
        'tests': tests
    }

async def info_for_sending_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, **kwargs):
    chosen_test_id = dialog_manager.dialog_data['chosen_test']
    info = dialog_manager.dialog_data['tests_data'][chosen_test_id]
    full_name = await db.get_str_full_name(student.telegram_id)
    class_title = await db.get_class_title(student.class_id)

    file_name = f'{info['course_title']} {info['test_title']} {class_title} {full_name} {student.variant}'
    dialog_manager.dialog_data['file_name'] = file_name
    folder_id = info['private_folder_id']
    dialog_manager.dialog_data['folder_id'] = folder_id

    time = await gd.get_latest_version_date(file_name, folder_id)
    if time is not None:
        time = convert_to_local_time(time)
    
    return {
        'time': time
    }

async def fail_text_getter(dialog_manager: DialogManager, **kwargs):
    text = dialog_manager.dialog_data['fail_text']
    return {
        'text': text
    }

async def sending_time_getter(dialog_manager: DialogManager, gd: GoogleDrive, **kwargs):
    file_name = dialog_manager.dialog_data['file_name']
    folder_id = dialog_manager.dialog_data['folder_id']
    time_iso = await gd.get_latest_version_date(file_name, folder_id)
    time = convert_to_local_time(time_iso) # type: ignore
    return {
        'time': time
    }

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

    # tasks = [process_lesson(lesson) for lesson in lessons_data]
    # lessons_info = await asyncio.gather(*tasks)
    
    # return {'lessons_info': lessons_info,
    #         'months_names': months_names,
    #         'courses': courses_data
    # }