from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dialogs.states import StartSG, SheetsSG
from db.views import StudentUser

router = Router()

@router.message(CommandStart())
async def start_message(message: Message, dialog_manager: DialogManager, admin_id: int, student: StudentUser | None):
    if not message.from_user:
        return
    
    telegram_id = message.from_user.id

    if telegram_id == admin_id:
        await dialog_manager.start(
            state=SheetsSG.start,
            mode=StartMode.RESET_STACK
        )

    elif student:
        await dialog_manager.start(
            state=StartSG.student,
            mode=StartMode.RESET_STACK,
        )
    else:
        await dialog_manager.start(
            state=StartSG.unknown_user,
            mode=StartMode.RESET_STACK
        )