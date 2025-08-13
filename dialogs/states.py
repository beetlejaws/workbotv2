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

class ScheduleSG(StatesGroup):
    show = State()

class SendWorkSG(StatesGroup):
    show_tests = State()
    start_sending = State()
    fail_sending = State()
    success_sending = State()

class SoonSG(StatesGroup):
    show = State()