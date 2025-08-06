from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dialogs.states import StartSG
from db.requests import Database

router = Router()

@router.message(CommandStart())
async def start_message(message: Message, dialog_manager: DialogManager, db: Database, admin_id: int):
    if not message.from_user:
        return
    
    telegram_id = message.from_user.id
    if telegram_id == admin_id:
        await dialog_manager.start(
            state=StartSG.admin,
            mode=StartMode.RESET_STACK
        )
    elif await db.get_student_id(telegram_id) is not None:
        await dialog_manager.start(
            state=StartSG.student,
            mode=StartMode.RESET_STACK
        )
    else:
        await dialog_manager.start(
            state=StartSG.unknown_user,
            mode=StartMode.RESET_STACK
        )