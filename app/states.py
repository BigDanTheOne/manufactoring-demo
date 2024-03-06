from aiogram.fsm.state import State, StatesGroup


class AccountStates(StatesGroup):
    contact_confirm = State()
    choose_line = State()
    choose_operator = State()
    choose_action = State()
    choose_order = State()
    choose_bundle = State()
    choose_product = State()
    enter_result = State()
    input_count = State()
    idle = State()
    idle_option = State()


class AdminStates(StatesGroup):
    main = State()
    add_operator = State()
    operator_rate = State()
    operator_line = State()
    add_account = State()
    account_role = State()
