from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dialogs.states import StartSG

router = Router()

@router.message(CommandStart())
async def start_message(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(
        state=StartSG.start,
        mode=StartMode.RESET_STACK
    )