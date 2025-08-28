from aiogram import Dispatcher
from aiogram_dialog import setup_dialogs

from dialogs.start_dialog import start_dialog
from dialogs.auth_dialog import auth_dialog
from dialogs.soon_dialog import soon_dialog
from dialogs.send_work_dialog import send_work_dialog
from dialogs.admin_dialog import sheets_dialog
from dialogs.schedule_dialog import schedule_dialog
from dialogs.settings_dialog import settings_dialog


def setup_my_dialogs(dp: Dispatcher) -> None:
    dp.include_router(start_dialog)
    dp.include_router(auth_dialog)
    dp.include_router(sheets_dialog)
    dp.include_router(schedule_dialog)
    dp.include_router(send_work_dialog)
    dp.include_router(soon_dialog)
    dp.include_router(settings_dialog)
    setup_dialogs(dp)