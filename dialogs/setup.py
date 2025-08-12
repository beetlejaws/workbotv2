from aiogram import Dispatcher
from dialogs.dialogs import *
from aiogram_dialog import setup_dialogs


def setup_my_dialogs(dp: Dispatcher) -> None:
    dp.include_router(start_dialog)
    dp.include_router(auth_dialog)
    dp.include_router(sheets_dialog)
    dp.include_router(schedule_dialog)
    dp.include_router(send_work_dialog)
    setup_dialogs(dp)