from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format, Case, List, Jinja
from aiogram_dialog.widgets.kbd import Button, Group, Select, Url, Multiselect, Radio
from aiogram_dialog.widgets.input import MessageInput
from dialogs.states import StartSG, SheetsSG
from dialogs.getters import *
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
        Const('Нажми на одну из кнопок, чтобы открыть необходимый тебе раздел'),
        Group(
            Button(
                Const('Ближайшее'),
                id='soon_tasks',
                on_click=go_soon_tasks
            ),
            Button(
                Const('🗓 Расписание'),
                id='go_schedule',
                on_click=go_schedule
            ),
            Url(
                Const('🗂 Google диск'),
                Format('https://drive.google.com/drive/folders/{folder_id}')
            ),
            Button(
                Const('Отправить работу'),
                id='start_sending_work',
                on_click=start_sending_work
            ),
            Button(
                Const('Настройки'),
                id='go_settings',
                on_click=go_settings
            )
        ),
        state=StartSG.student,
        getter=folder_id_getter
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
        parse_mode='HTML',
        state=ScheduleSG.show,
        getter=schedule_getter
    )
)

