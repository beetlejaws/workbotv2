from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select
from dialogs.states import SheetsSG
from db.requests import Database
from services.google_services import GoogleSheets


async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()

async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()

async def go_to_sheets(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=SheetsSG.start)

async def close_dialog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()

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