from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()

class SheetsSG(StatesGroup):
    start = State()