from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Group, Select
from aiogram_dialog.widgets.input import MessageInput
from dialogs.states import StartSG, SheetsSG
from dialogs.getters import get_sheets_data
from dialogs.handlers import *


start_dialog = Dialog(
    Window(
        Const('Привет! Тебя ещё нет в моей базе. Для того, чтобы начать работу со мной, тебе нужно пройти авторизацию.'),
        Button(
            text=Const('Пройти авторизацию'),
            id='auth_btn',
            on_click=start_auth
        ),
        state=StartSG.unknown_user
    ),
    Window(
        Const('Ты студент'),
        state=StartSG.student
    ),
    Window(
        Const('Ты админ'),
        state=StartSG.admin
    )
)

auth_dialog = Dialog(
    Window(
        Const('Пожалуйста, введи свой идентификационный номер'),
        MessageInput(
            func=student_id_check,
            content_types=ContentType.TEXT,
        ),
        MessageInput(
            func=fail_auth,
            content_types=ContentType.ANY,
        ),
        state=AuthSG.start
    ),
    Window(
        Const('К сожалению, введённый номер не найден. Попробуй ещё раз, заново отправив команду /start'),
        MessageInput(
            func=student_id_check,
            content_types=ContentType.TEXT,
        ),
        MessageInput(
            func=fail_auth,
            content_types=ContentType.ANY,
        ),
        state=AuthSG.fail
    ),
    Window(
        Format('Готово! Я записал тебя под именем {dialog_data[full_name]}.'),
        Button(
            Const('Старт'),
            id='go_start',
            on_click=go_start
        ),
        state=AuthSG.success
    )
)

sheets_dialog = Dialog(
    Window(
        Const('Выбери таблицу, которую нужно обновить'),
        Group(
            Select(
                Format('{item[0]}'),
                id='sheets',
                item_id_getter=lambda x: x[0],
                items='sheets_data',
                on_click=sheet_selection
            ),
            width=2
        ),
        Button(
            text=Const('Назад'),
            id='back',
            on_click=close_dialog
        ),
        getter=get_sheets_data,
        state=SheetsSG.start
    )
)