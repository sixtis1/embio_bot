import keyboards.constants as kc

from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import (
    ReplyKeyboardBuilder,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)


def main_admin_kb():
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        KeyboardButton(text=kc.buttons_admin_menu["send_script"]),
        KeyboardButton(text=kc.buttons_admin_menu["change_script"]),
    )

    keyboard.row(KeyboardButton(text=kc.buttons_admin_menu["find_patient"]))

    return keyboard.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите действие"
    )


def changes_admin_kb():
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        KeyboardButton(text=kc.buttons_admin_changes["change_patient_script"]),
        KeyboardButton(text=kc.buttons_admin_changes["change_general_script"]),
    )

    keyboard.row(KeyboardButton(text=kc.buttons_admin_changes["back_to_menu"]))

    return keyboard.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите действие"
    )


def find_admin_kb():
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        KeyboardButton(text=kc.buttons_admin_find["find_by_surname"]),
        KeyboardButton(text=kc.buttons_admin_find["find_by_doctor"]),
    )

    keyboard.row(KeyboardButton(text=kc.buttons_admin_find["find_by_phone"]))

    keyboard.row(KeyboardButton(text=kc.buttons_admin_find["back_to_menu"]))

    return keyboard.as_markup(
        resize_keyboard=True, input_field_placeholder="Выберите действие"
    )


def inline_doctors_keyboard(directory):
    if directory is None or directory.get("result") is None:
        return InlineKeyboardMarkup(inline_keyboard=[])

    doctors_list = directory["result"]["items"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{doctor['doctor_name']}",
                    callback_data=f"{doctor['doctor_id']}",
                )
            ]
            for doctor in doctors_list
        ]
    )
    return keyboard


def inline_patients_keyboard(directory, by_what):
    if directory is None or directory.get("result") is None:
        return InlineKeyboardMarkup(inline_keyboard=[])

    patient_list = directory["result"]["items"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{patient['patient_name']}",
                    callback_data=f"{patient['patient_id']}",
                )
            ]
            for patient in patient_list
        ]
    )
    if by_what != "surname":
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="Вернуться к выбору врача",
                    callback_data="back_to_doctors",
                )
            ]
        )
    return keyboard


def inline_scenario_selection_keyboard(scenarios):
    if scenarios is None or scenarios.get("result") is None:
        return InlineKeyboardMarkup(inline_keyboard=[])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=scenario["name_stage"],
                    callback_data=f"change_scenario_{scenario['scenario_id']}",
                )
            ]
            for scenario in scenarios["result"]["items"]
        ]
    )
    return keyboard


def back_to_menu_kb():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=kc.buttons_admin_back["back"]))
    return keyboard.as_markup(resize_keyboard=True)


def back_to_messages_kb():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Назад"))
    return keyboard.as_markup(resize_keyboard=True)


def yes_no_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=kc.buttons_yn["yes"]))
    keyboard.add(KeyboardButton(text=kc.buttons_yn["no"]))
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=True)


def edit_global_choice_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сообщение", callback_data="edit_message"),
                InlineKeyboardButton(text="Время", callback_data="edit_time"),
            ]
        ]
    )
    return keyboard
