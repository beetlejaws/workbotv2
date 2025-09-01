from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Group, Url, Start, Cancel

from db.requests import Database
from db.views import StudentUser
from services.google_services import GoogleDrive

from dialogs.states import *

#getters
async def folder_link_getter(dialog_manager: DialogManager, db: Database, gd: GoogleDrive, student: StudentUser, **kwargs):
    folder_id = await db.get_class_folder_id(student.class_id)
    folder_link = gd.get_folder_link(folder_id)
    return {'folder_link': folder_link}

start_dialog = Dialog(
    Window(
        Const('Привет! Тебя ещё нет в моей базе. Для того, чтобы начать работу со мной, тебе нужно пройти авторизацию.'),
        Start(
            text=Const('Пройти авторизацию'),
            id='auth_btn',
            state=AuthSG.start
        ),
        state=StartSG.unknown_user
    ),
    Window(
        Const('Нажми на одну из кнопок, чтобы открыть необходимый тебе раздел'),
        Group(
            Start(
                text=Const('🔜 Ближайшее'),
                id='soon_tasks',
                state=SoonSG.show
            ),
            Start(
                Const('🗓 Расписание'),
                id='go_schedule',
                state=ScheduleSG.show
            ),
            Url(
                Const('🗂 Google диск'),
                Format('{folder_link}')
            ),
            Start(
                Const('📎 Отправить работу'),
                id='start_sending_work',
                state=SendWorkSG.show_tests
            ),
            Start(
                text=Const('🔔 Настроить уведомления'),
                id='settings',
                state=SettingsSG.show
            )
        ),
        state=StartSG.student,
        getter=folder_link_getter
    ),
    Window(
        Const('Ты админ'),
        state=StartSG.admin
    )
)