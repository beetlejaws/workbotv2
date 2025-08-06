from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    admin = State()
    student = State()
    unknown_user = State()


class AuthSG(StatesGroup):
    start = State()
    success = State()
    fail = State()


class SheetsSG(StatesGroup):
    start = State()