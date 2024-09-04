from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from keyboards.constants import button_auth_find


# клавиатура для запроса номера телефона
def get_phone_keyboard():
    button = KeyboardButton(text=button_auth_find["share_phone"], request_contact=True)
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    return keyboard
