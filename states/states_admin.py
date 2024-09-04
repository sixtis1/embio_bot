from aiogram.fsm.state import StatesGroup, State


# Главные стейты для выбора возможного действия
class AdminStates_global(StatesGroup):
    edit_message = State()
    menu = State()
    send_script = State()
    change_script = State()
    find_patient = State()
    edit_script_message = State()
    waiting_for_more_messages = State()
    waiting_for_more_editing = State()
    edit_script_time = State()
    choose_edit_option = State()
    select_message = State()
    waiting_for_stage = State()


# Стейты для отслеживания выбора поиска
class AdminStates_find(StatesGroup):
    surname = State()
    doctor_name_first = State()
    doctor_name_second = State()
    telephone = State()


class AdminStates_changes(StatesGroup):
    select_message = State()
    find_patient_scenarios = State()
    change_find_scenarios = State()
    change_one_first = State()
    change_one_second = State()
    confirm_edit = State()
    message_or_time = State()


class SendScenarioStates(StatesGroup):
    waiting_for_phone_number = State()
    waiting_for_message_number = State()
    waiting_for_stage = State()
