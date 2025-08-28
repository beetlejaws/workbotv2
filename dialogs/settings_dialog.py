from aiogram.types import CallbackQuery

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button, Cancel

from db.requests import Database
from db.views import StudentUser

from dialogs.states import SettingsSG
from dialogs.utils import radio_check_choice


#handlers
async def change_sub_status(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    db: Database = dialog_manager.middleware_data['db']
    if 'lesson' in widget.widget_id: 
        new_status = await db.change_sub_status(dialog_manager.dialog_data['student_id'], 'lesson')
        dialog_manager.dialog_data['lesson_status'] = new_status
    else:
        new_status = await db.change_sub_status(dialog_manager.dialog_data['student_id'], 'deadline')
        dialog_manager.dialog_data['deadline_status'] = new_status

#getters
async def sub_status_getter(dialog_manager: DialogManager, db: Database, student: StudentUser, **kwargs):
    
    dialog_manager.dialog_data['student_id'] = student.id
    if dialog_manager.dialog_data.get('lesson_status') is None:
        dialog_manager.dialog_data['lesson_status'] = student.lesson_sub

    if dialog_manager.dialog_data.get('deadline_status') is None:
        dialog_manager.dialog_data['deadline_status'] = student.deadlines_sub

    lesson_status = dialog_manager.dialog_data['lesson_status']
    deadline_status = dialog_manager.dialog_data['deadline_status']

    return {
        'lesson_sub_status': lesson_status,
        'lesson_unsub_status': not lesson_status,
        'deadline_sub_status': deadline_status,
        'deadline_unsub_status': not deadline_status
    }


settings_dialog = Dialog(
    Window(
        Const(
            text=
'''Здесь ты можешь включать и отключать уведомления по грядущим занятиям и дедлайнам.
✅ - уведомления включены
❌ - уведомления отключены'''
        ),
        Button(
            text=Const('✅ Занятия на завтра'),
            id='lesson_sub_status',
            when='lesson_sub_status',
            on_click=change_sub_status
        ),
        Button(
            text=Const('❌ Занятия на завтра'),
            id='lesson_unsub_status',
            when='lesson_unsub_status',
            on_click=change_sub_status
        ),
        Button(
            text=Const('✅ Дедлайны'),
            id='deadline_sub_status',
            when='deadline_sub_status',
            on_click=change_sub_status
        ),
        Button(
            text=Const('❌ Дедлайны'),
            id='deadline_unsub_status',
            when='deadline_unsub_status',
            on_click=change_sub_status
        ),
        Cancel(
            text=Const('Назад')
        ),
        state=SettingsSG.show,
        getter=sub_status_getter
    )
)
