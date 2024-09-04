from aiogram.fsm.state import StatesGroup, State


# стейты для авторизации
class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_additional_info = State()
