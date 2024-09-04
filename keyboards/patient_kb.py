import keyboards.constants as kc
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def patient_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=kc.buttons_patient_menu["schedule"])],
            [KeyboardButton(text=kc.buttons_patient_menu["question"])],
        ],
        resize_keyboard=True,
    )
    return keyboard


def patient_question_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=kc.buttons_patient_question["back"])]],
        resize_keyboard=True,
    )
    return keyboard


def patient_question_cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=kc.buttons_patient_cancel["schedule"])],
            [KeyboardButton(text=kc.buttons_patient_cancel["cancel_question"])],
        ],
        resize_keyboard=True,
    )
    return keyboard


def no_question_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=kc.buttons_patient_no_question["no question"])]],
        resize_keyboard=True,
    )
    return keyboard


async def inline_survey(answers):
    keyboard = InlineKeyboardBuilder()
    for answer in answers:
        keyboard.add(
            InlineKeyboardButton(
                text=answers[answer]["text"],
                callback_data=answer,
            )
        )
    return keyboard.adjust(1).as_markup()


async def inline_preparations(preparations):
    keyboard = InlineKeyboardBuilder()
    for preparation in preparations:
        keyboard.add(
            InlineKeyboardButton(
                text=preparations[preparation],
                callback_data=str(preparation),
            )
        )
    return keyboard.adjust(1).as_markup()


def yes_or_no():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=kc.buttons_patient_yes_or_no["yes"]),
                KeyboardButton(text=kc.buttons_patient_yes_or_no["no"]),
            ]
        ],
        resize_keyboard=True,
    )
    return keyboard
