import logging

from aiogram.types import Message, CallbackQuery, ContentType

from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Start
from aiogram_dialog.widgets.input import MessageInput

from db.requests import Database

from dialogs.states import AuthSG, StartSG


logger = logging.getLogger(__name__)


#handlers
async def student_id_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    
    db: Database = dialog_manager.middleware_data['db']
    telegram_id = dialog_manager.middleware_data['telegram_id']

    try:
        student_id = int(message.text)
        student = await db.add_telegram_id(student_id, telegram_id)
        print(student)
        dialog_manager.dialog_data['full_name'] = student.full_name
        logger.info(f'STUDENT: Новый пользователь {student.full_name}\n "tg://openmessage?user_id={telegram_id}"')
        await dialog_manager.switch_to(AuthSG.success)
    except:
        await dialog_manager.switch_to(AuthSG.fail)

async def fail_auth(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    await dialog_manager.switch_to(AuthSG.fail)

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
        Start(
            text=Const('Старт'),
            id='start',
            state=StartSG.student,
            mode=StartMode.RESET_STACK),
        state=AuthSG.success
    )
)