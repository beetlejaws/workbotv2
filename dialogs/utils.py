from typing import Any
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import ManagedRadio


async def radio_check_choice(dialog_manager: DialogManager, radio_id: str, key: str, default_value: Any) -> Any:
        if dialog_manager.dialog_data.get(key) is None:
            checked_value = dialog_manager.dialog_data[key] = default_value
            radio: ManagedRadio = dialog_manager.find(radio_id)
            await radio.set_checked(checked_value)
        else:
            checked_value = dialog_manager.dialog_data[key]
        return checked_value