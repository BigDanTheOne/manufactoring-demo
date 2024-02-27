from aiogram.fsm.state import State, StatesGroup


class MainStates(StatesGroup):
    contact_confirm = State()
    choose_line = State()
    choose_employee = State()
    choose_action = State()
    choose_order = State()
    choose_bundle = State()
    choose_product = State()
    enter_result = State()
    input_count = State()
    idle = State()
    idle_option = State()
