from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    setup_language = State()
