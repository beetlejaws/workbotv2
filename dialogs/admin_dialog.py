from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Group, Select, Cancel

from db.requests import Database
from services.google_services import GoogleSheets

from dialogs.states import *


#handlers
async def sheet_selection(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    db: Database = dialog_manager.middleware_data['db']
    gs: GoogleSheets = dialog_manager.middleware_data['gs']
    sheets_ids = dialog_manager.middleware_data['sheets_ids']
    sheet_name, sheet_id = item_id, sheets_ids[item_id]

    if await db.update_table(sheet_name, await gs.get_sheet_data(sheet_id)):
        await callback.answer(
            text='Таблица успешно обновлена',
            show_alert=True
            )
    else:
        await callback.answer(
            text='Произошла ошибка при обновлении',
            show_alert=True
            )
        
#getters
async def get_sheets_data(dialog_manager: DialogManager, sheets_ids: dict, **kwargs):
    sheets_data = list(sheets_ids.items())
    return {'sheets_data': sheets_data}


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
        Cancel(
            text=Const('Назад')
        ),
        getter=get_sheets_data,
        state=SheetsSG.start
    )
)