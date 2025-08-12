
from io import BytesIO
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InaccessibleMessage
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button, Select, Multiselect, ManagedMultiselect, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from dialogs.states import *
from db.requests import Database
from services.google_services import GoogleSheets, GoogleDrive


async def start_auth(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    if callback.message and not isinstance(callback.message, InaccessibleMessage):
        await callback.message.edit_reply_markup(reply_markup=None)
    await dialog_manager.start(AuthSG.start)

async def student_id_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    db: Database = dialog_manager.middleware_data['db']
    telegram_id = dialog_manager.middleware_data['telegram_id']
    if message.text:
        student_id = int(message.text)
        try:
            await db.add_telegram_id(student_id, telegram_id)
            dialog_manager.dialog_data['full_name'] = await db.get_str_full_name(telegram_id)
            await dialog_manager.switch_to(AuthSG.success)
        except:
            await dialog_manager.switch_to(AuthSG.fail)

async def fail_auth(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    await dialog_manager.switch_to(AuthSG.fail)

async def go_start(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    if callback.from_user.id == dialog_manager.middleware_data['admin_id']:
        await dialog_manager.start(
            state=StartSG.admin,
            mode=StartMode.RESET_STACK)
    else:
        await dialog_manager.start(
            state=StartSG.student,
            mode=StartMode.RESET_STACK
            )

async def go_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.back()

async def go_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.next()

async def go_soon_tasks(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()

async def go_schedule(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(ScheduleSG.show)

async def start_sending_work(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(SendWorkSG.show_tests)

async def go_settings(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()

async def go_to_sheets(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(SheetsSG.start)

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
        
async def month_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['current_month'] = int(item_id)

# async def courses_selection(callback: CallbackQuery, widget: ManagedMultiselect, dialog_manager: DialogManager, item_id: str):
#     chosen_courses: list = dialog_manager.dialog_data['chosen_courses']
#     if int(item_id) in chosen_courses:
#         chosen_courses.remove(int(item_id))
#     else:
#         chosen_courses.append(int(item_id))
#         chosen_courses.sort()
#     dialog_manager.dialog_data['chosen_courses'] = chosen_courses

async def course_selection(callback: CallbackQuery, widget: ManagedRadio, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_course'] = int(item_id)

async def choose_sending_work(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    dialog_manager.dialog_data['chosen_test'] = int(item_id)
    await dialog_manager.next()

async def document_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    bot: Bot = dialog_manager.middleware_data['bot']
    MAX_FILE_SIZE = 20 * 1024 * 1024
    document = message.document
    if not document:
        return
    
    file_size = document.file_size
    file_info = await bot.get_file(document.file_id)
    file = await bot.download_file(file_info.file_path) # type: ignore

    if file_size > MAX_FILE_SIZE: # type: ignore
        dialog_manager.dialog_data['fail_text'] = 'Этот файл слишком большой. Отправь файл весом не более 20MB'
        await dialog_manager.switch_to(SendWorkSG.fail_sending)
    elif document.mime_type != 'application/pdf':
        dialog_manager.dialog_data['fail_text'] = 'Я принимаю файлы только в формате PDF. Отправь файл ещё раз в нужном формате'
        await dialog_manager.next()
    else:
        file_name = dialog_manager.dialog_data['file_name']
        folder_id = dialog_manager.dialog_data['folder_id']
        file_content = BytesIO(file.read()) # type: ignore
        gd: GoogleDrive = dialog_manager.middleware_data['gd']
        previous_versions = await gd.get_files_by_name(file_name, folder_id)
        if len(previous_versions) > 0:
            file_name += f'_v{len(previous_versions) + 1}'

        await gd.upload_file(f'{file_name}.pdf', file_content, folder_id)

        await dialog_manager.switch_to(SendWorkSG.success_sending)

async def fail_document_check(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data['fail_text'] = '''В качестве решения я принимаю только файл. 
Отправь мне файл с решением в формате PDF и размером не более 20MB или нажми кнопку "Отмена"'''
    await dialog_manager.switch_to(SendWorkSG.fail_sending)
