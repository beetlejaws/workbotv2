from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Group, Select
from dialogs.states import StartSG, SheetsSG
from dialogs.getters import username_getter, get_sheets_data
from dialogs.handlers import go_to_sheets, go_next, go_back, close_dialog, sheet_selection


start_dialog = Dialog(
    Window(
        Format('Привет, {username}. Нажми кнопку "Старт".'),
        Button(
            text=Const('Таблицы'),
            id='sheets_btn',
            on_click=go_to_sheets
        ),
        getter=username_getter,
        state=StartSG.start
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