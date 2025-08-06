from aiogram.types import User
from aiogram_dialog import DialogManager
from db.requests import Database
from services.google_services import GoogleSheets


async def telegram_id_getter(dialog_manager: DialogManager, event_from_user: User, **kwargs):
    event_from_user.username

async def get_sheets_data(dialog_manager: DialogManager, sheets_ids: dict, **kwargs):
    sheets_data = list(sheets_ids.items())
    return {'sheets_data': sheets_data}