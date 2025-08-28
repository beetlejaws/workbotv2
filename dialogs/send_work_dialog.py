from utils.utils import *
from io import BytesIO
import json

from aiogram import Bot
from aiogram.types import Message, CallbackQuery, ContentType

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format, Case
from aiogram_dialog.widgets.kbd import Button, Group, Select, SwitchTo, Back, Cancel
from aiogram_dialog.widgets.input import MessageInput

from db.requests import Database
from db.views import StudentUser, Test
from services.google_services import GoogleDrive

from dialogs.states import SendWorkSG


#handlers
async def choose_sending_work(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_index'] = int(item_id)
    await dialog_manager.next()

async def document_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    bot: Bot = dialog_manager.middleware_data['bot']
    MAX_FILE_SIZE = 20 * 1024 * 1024
    document = message.document
    if not document:
        return
    
    file_size = document.file_size
    file_info = await bot.get_file(document.file_id)
    file = await bot.download_file(file_info.file_path)

    if file_size > MAX_FILE_SIZE:
        dialog_manager.dialog_data['fail_text'] = 'Этот файл слишком большой. Отправь файл весом не более 20MB'
        await dialog_manager.switch_to(SendWorkSG.fail_sending)
    elif document.mime_type != 'application/pdf':
        dialog_manager.dialog_data['fail_text'] = 'Я принимаю файлы только в формате PDF. Отправь файл ещё раз в нужном формате'
        await dialog_manager.next()
    else:
        file_name = dialog_manager.dialog_data['file_name']
        folder_id = dialog_manager.dialog_data['folder_id']
        file_content = BytesIO(file.read())
        gd: GoogleDrive = dialog_manager.middleware_data['gd']
        previous_versions = await gd.get_files_by_name(file_name, folder_id)
        if len(previous_versions) > 0:
            file_name += f'_v{len(previous_versions) + 1}'

        await gd.upload_file(f'{file_name}.pdf', file_content, folder_id)

        await dialog_manager.switch_to(SendWorkSG.success_sending)

async def fail_document_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['fail_text'] = '''В качестве решения я принимаю только файл. 
Отправь мне файл с решением в формате PDF и размером не более 20MB или нажми кнопку "Отмена"'''
    await dialog_manager.switch_to(SendWorkSG.fail_sending)

#getters
async def send_work_getter(dialog_manager: DialogManager, db: Database, student: StudentUser, **kwargs):
    tests_list: list[Test] = await db.get_active_tests(student.class_id)
    if tests_list:
        show_mode = True
        dialog_manager.dialog_data['tests_data'] = json.dumps([test.model_dump(mode='json') for test in tests_list])
        tests = [(index, test.course_title, test.title) for index, test in enumerate(tests_list)]
    else:
        show_mode = False
        tests = None

    return {
        'show_mode': show_mode,
        'tests': tests
    }

async def info_for_sending_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, **kwargs):
    chosen_index = dialog_manager.dialog_data['chosen_index']
    tests = [Test(**s) for s in json.loads(dialog_manager.dialog_data['tests_data'])]
    test: Test = tests[chosen_index]

    file_name = f'{test.course_title} {test.title} {student.class_title} {student.full_name} {student.variant}'
    dialog_manager.dialog_data['file_name'] = file_name
    folder_id = test.private_folder_id
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


send_work_dialog = Dialog(
    Window(
        Case(
            texts={
                True: Const('Выбери работу, решение которой хочешь отправить'),
                False: Const('Сейчас нет доступной работы, решение которой можно отправить')
            },
            selector='show_mode'
        ),
        Group(
            Select(
                Format('{item[1]} {item[2]}'),
                id='test',
                item_id_getter=lambda x: x[0],
                items='tests',
                when='show_mode',
                on_click=choose_sending_work
            ),
            width=1
        ),
        Cancel(
            text=Const('⬅️ Назад'),
        ),
        state=SendWorkSG.show_tests,
        getter=send_work_getter
    ),
    Window(
        Format(
            text='Прошлое решение было отправлено {time}',
            when='time'
        ),
        Const('Отправь мне файл с решением в формате PDF и размером не более 20MB или нажми кнопку "Отмена"'),
        MessageInput(
            func=document_check,
            content_types=ContentType.DOCUMENT,
        ),
        MessageInput(
            func=fail_document_check,
            content_types=ContentType.ANY,
        ),
        Back(
            text=Const('Отмена')
        ),
        state=SendWorkSG.start_sending,
        getter=info_for_sending_getter
    ),
    Window(
        Format('{text}'),
        MessageInput(
            func=document_check,
            content_types=ContentType.DOCUMENT,
        ),
        MessageInput(
            func=fail_document_check,
            content_types=ContentType.ANY,
        ),
        SwitchTo(
            text=Const('Отмена'),
            id='cancel_btn',
            state=SendWorkSG.show_tests
        ),
        state=SendWorkSG.fail_sending,
        getter=fail_text_getter
    ),
    Window(
        Format('Файл отправлен. Время отправления - {time}'),
        SwitchTo(
            text=Const('Вернуться'),
            id='back',
            state=SendWorkSG.show_tests
        ),
        state=SendWorkSG.success_sending,
        getter=sending_time_getter
    )
)