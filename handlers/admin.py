import re
from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import keyboards.admin_kb as kb
import keyboards.constants as kc
import handlers.format_functions.admins_functions as hf
from configuration.config_db import get_client

from database.admin_db import (
    find_all_doctors,
    find_all_patients,
    get_all_scenarios,
    find_patient_scenarios,
    logger,
    get_scenario_data,
)

from states.states_admin import (
    AdminStates_global,
    AdminStates_find,
    AdminStates_changes,
    SendScenarioStates,
)

admin_router = Router()
supabase = get_client()
global all_patients, prompt_message, all_doctors, scenarios, edditing_text, number, choice
all_patients, all_doctors, scenarios = None, None, None
back_to_choice = "Возвращаю вас к выбору сценария..."
choice_action = "Выберите нужное действие"


@admin_router.message(
    F.text == kc.buttons_admin_back["back"],
    StateFilter(
        AdminStates_global.change_script,
        AdminStates_changes.find_patient_scenarios,
        AdminStates_changes.change_one_first,
        AdminStates_global.choose_edit_option,
        AdminStates_changes.select_message,
        AdminStates_global.edit_script_message,
        AdminStates_global.edit_script_time,
    ),
)
async def back_to_menu(message: Message, state: FSMContext):
    global all_patients, all_doctors, scenarios
    all_patients, all_doctors, scenarios = None, None, None
    await hf.reset_information(state, message)
    await state.set_state(AdminStates_global.change_script)
    await message.answer(
        "Что именно вы хотите сделать?", reply_markup=kb.changes_admin_kb()
    )


@admin_router.message(
    F.text == kc.buttons_admin_back["back"],
    StateFilter(
        AdminStates_global.find_patient,
        AdminStates_find.doctor_name_first,
        AdminStates_find.doctor_name_second,
        AdminStates_find.surname,
        AdminStates_find.telephone,
    ),
)
async def back_to_menu(message: Message, state: FSMContext):
    global all_patients, all_doctors, scenarios
    all_patients, all_doctors, scenarios = None, None, None
    await hf.reset_information(state, message)
    await state.set_state(AdminStates_global.find_patient)
    await message.answer(
        "Что именно вы хотите сделать?", reply_markup=kb.find_admin_kb()
    )


async def command_admin(message: Message, state: FSMContext):
    await message.answer(
        text="Добро пожаловать, админ! Здесь вы можете посмотреть информацию о пациентах, отправить или отредактировать "
        "сценарий.",
        reply_markup=kb.main_admin_kb(),
    )
    await state.set_state(AdminStates_global.menu)


@admin_router.message(
    AdminStates_global.menu, F.text == kc.buttons_admin_menu["send_script"]
)
async def send_admin(message: Message, state: FSMContext):
    await message.answer(
        "Введите номер телефона пациента в формате +7XXXXXXXXXX:",
        reply_markup=kb.back_to_messages_kb(),
    )
    await state.set_state(AdminStates_global.send_script)


@admin_router.message(
    AdminStates_global.menu,
    F.text == kc.buttons_admin_menu["change_script"],
)
async def change_admin(message: Message, state: FSMContext):
    await message.answer(
        "Здесь вы можете изменить сценарий как конкретного пациента, так и общий. "
        "Что конкретно вы хотите изменить?",
        reply_markup=kb.changes_admin_kb(),
    )
    await state.set_state(AdminStates_global.change_script)


@admin_router.message(
    AdminStates_global.menu,
    F.text == kc.buttons_admin_menu["find_patient"],
)
async def find_admin(message: Message, state: FSMContext):
    await message.answer(
        "Здесь вы можете найти пациента по трем параметрам: его фамилии, его номеру телефона и по врачу, к которому "
        "он привязан.",
        reply_markup=kb.find_admin_kb(),
    )
    await message.answer("Как именно вы хотите найти пациента?")
    await state.set_state(AdminStates_global.find_patient)


@admin_router.message(
    F.text == kc.buttons_admin_changes["back_to_menu"],
)
async def back_to(message: Message, state: FSMContext):
    await message.answer(choice_action, reply_markup=kb.main_admin_kb())
    await state.set_state(AdminStates_global.menu)


@admin_router.callback_query(
    AdminStates_global.waiting_for_stage, F.data.startswith("change_scenario_")
)
async def handle_stage_selection(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.answer()
    scenario_id = int(callback_query.data.split("_")[-1])

    try:
        scenario_data = await get_scenario_data(scenario_id)
        if not scenario_data or "messages" not in scenario_data:
            await callback_query.message.answer(
                "Ошибка при получении данных сценария. Попробуйте позже."
            )
            return

        await state.update_data(
            scenario_id=scenario_id, messages=scenario_data["messages"]
        )

        # Отправляем список сообщений
        await hf.send_message_list(callback_query.message, state)

        # Переходим к следующему шагу
        await state.set_state(SendScenarioStates.waiting_for_message_number)

    except Exception as e:
        logger.exception(f"Ошибка при выборе сценария:{e}")
        await callback_query.message.answer(
            "Произошла ошибка при получении данных сценария. Попробуйте снова.",
            reply_markup=kb.back_to_messages_kb(),
        )


@admin_router.message(AdminStates_global.send_script)
async def process_phone_number_wrapper(message: types.Message, state: FSMContext):
    await hf.process_phone_number(message, state, back_to)


@admin_router.message(SendScenarioStates.waiting_for_message_number)
async def process_message_number_wrapper(message: types.Message, state: FSMContext):
    data = await state.get_data()
    id = data.get("scenario_id")
    await hf.process_message_number(message, state, back_to, id)


@admin_router.message(F.text == "Да", AdminStates_global.waiting_for_more_messages)
async def handle_send_more(message: Message, state: FSMContext):
    await message.answer(
        "Введите номер телефона пациента в формате +7XXXXXXXXXX:",
        reply_markup=kb.back_to_messages_kb(),
    )
    await state.set_state(AdminStates_global.send_script)


@admin_router.message(F.text == "Нет", AdminStates_global.waiting_for_more_messages)
async def handle_stop_sending(message: Message, state: FSMContext):
    await message.answer(choice_action, reply_markup=kb.main_admin_kb())
    await state.set_state(AdminStates_global.menu)


@admin_router.message(
    AdminStates_global.change_script,
    F.text == kc.buttons_admin_changes["change_patient_script"],
)
async def change_patient(message: Message, state: FSMContext):
    prompt_message = await message.answer(
        "Введите номер в формате +7XXXXXXXXXX", reply_markup=kb.back_to_menu_kb()
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates_changes.find_patient_scenarios)


@admin_router.message(AdminStates_changes.find_patient_scenarios)
async def find_patient_now_scenarios(message: Message, state: FSMContext):
    global scenarios
    information = message.text
    if scenarios is None:
        scenarios = await find_patient_scenarios(information)
    if scenarios and "result" in scenarios and scenarios["result"].get("code") == 0:
        scenario_items = scenarios["result"]["items"]
        for scenario in scenario_items:
            name_stage = scenario["name_stage"]  # Извлечение 'name_stage'
            current_part = (
                f"Найден следующий сценарий у данного пациента: '{name_stage}'\n\n"
            )
            response_text = hf.format_scenarios(current_part, scenario_items)
            for part in response_text:
                await message.answer(part)
            await message.answer(
                "Напишите номер сообщения, которое вы хотите изменить."
            )
            await state.set_state(AdminStates_changes.change_one_first)
    else:
        information = None
        scenarios = None
        await message.answer(
            "Пациент с таким номером телефона не найден. Пожалуйста, попробуйте снова ввести номер телефона."
        )
        await state.set_state(AdminStates_global.change_script)
        await change_patient(message, state)


@admin_router.message(AdminStates_changes.change_one_first)
async def editing_message_first(message: Message, state: FSMContext):
    global number, scenarios
    number = message.text
    if number.isdigit() and any(
        1 <= int(number) <= len(scenario["messages"])
        for scenario in scenarios["result"]["items"]
    ):
        found_message = next(
            (
                msg
                for scenario in scenarios["result"]["items"]
                for msg in scenario["messages"]
                if msg["id"] == int(number)
            ),
            None,
        )
        await message.answer(
            f"Вы выбрали сообщение для редактирования: {found_message['content']}",
            reply_markup=kb.back_to_messages_kb(),
        )
        await message.answer(f"Время отправки сообщения: {found_message['time']}")
        prompt_message = await message.answer(
            "Теперь скажите, что вы хотите изменить: время отправки или содержимое сообщения?",
            reply_markup=kb.edit_global_choice_keyboard(),
        )
        await state.update_data(prompt_message_id=prompt_message.message_id)
        await state.set_state(AdminStates_changes.message_or_time)
    else:
        await message.answer(
            "Сообщение с указанным номером не существует. Пожалуйста, введите корректный номер сообщения."
        )
        return


@admin_router.callback_query(
    AdminStates_changes.message_or_time, F.data.in_(["edit_message", "edit_time"])
)
async def what_need_changes(query: CallbackQuery, state: FSMContext):
    global choice
    choice = query.data
    await hf.edditing_message_or_time(query, choice)
    await state.set_state(AdminStates_changes.change_one_second)


@admin_router.message(AdminStates_changes.message_or_time, F.text == "Назад")
async def edditing_back(message: Message, state: FSMContext):
    await state.set_state(AdminStates_changes.find_patient_scenarios)
    await message.answer(
        "Возвращаю вас к выбору сообщения...", reply_markup=kb.back_to_menu_kb()
    )
    await find_patient_now_scenarios(message, state)


@admin_router.message(AdminStates_changes.change_one_second, F.text == "Назад")
async def edditing_back(message: Message, state: FSMContext):
    await state.set_state(AdminStates_changes.message_or_time)
    await message.answer("Возвращаю вас к выбору...")
    await message.answer(
        "Скажите, что вы хотите изменить: время отправки или содержимое сообщения?",
        reply_markup=kb.edit_global_choice_keyboard(),
    )


@admin_router.message(AdminStates_changes.change_one_second, F.text != "Назад")
async def editing_message_second(message: Message, state: FSMContext):
    global scenarios, number, edditing_text, choice
    edditing_text = message.text
    valid = None
    match choice:
        case "edit_message":
            await message.answer(
                f"Изменяю сообщение в текущем сценарии на следующее: '{edditing_text}'"
            )
            valid = True  # Предполагаем, что текст всегда валидный
        case "edit_time":
            # Регулярное выражение для проверки формата времени
            time_pattern = r"^[+-]?\d+(\s\d{2}:\d{2})?$"
            if re.match(time_pattern, edditing_text):
                await message.answer(
                    f"Изменяю время отправки на следующее: {edditing_text}"
                )
                valid = True
            else:
                await message.answer(
                    "Некорректный формат времени. Пожалуйста, введите в формате: (+/-)2 10:00 или (+/-)2"
                )
                valid = False
    if valid:
        try:
            result = await hf.changin_scenario_in_bd(
                scenarios, number, edditing_text, choice
            )
            if result.get("status") == "success":
                await message.answer("Сценарий успешно обновлен.")
            else:
                await message.answer(
                    "Возникла ошибка. Возможно проблемы с сохранением в базу данных("
                )
            await message.answer(
                "Хотите продолжить редактирование других сообщений данного пациента?",
                reply_markup=kb.yes_no_keyboard(),
            )
            await state.set_state(AdminStates_changes.confirm_edit)
        except Exception as e:
            logger.exception(f"Возникла ошибка: {str(e)}")
    else:
        await message.answer("Попробуйте снова ввести корректные данные.")


@admin_router.message(AdminStates_changes.confirm_edit, F.text == kc.buttons_yn["yes"])
async def yes_edditing_scenarios(message: Message, state: FSMContext):
    await state.set_state(AdminStates_changes.find_patient_scenarios)
    await message.answer(
        "Возвращаю вас к выбору сообщения...", reply_markup=kb.back_to_menu_kb()
    )
    await find_patient_now_scenarios(message, state)


@admin_router.message(AdminStates_changes.confirm_edit, F.text == kc.buttons_yn["no"])
async def no_edditing_scenarios(message: Message, state: FSMContext):
    await state.set_state(AdminStates_global.change_script)
    await message.answer(
        "Что конкретно вы хотите изменить?", reply_markup=kb.changes_admin_kb()
    )


@admin_router.message(
    AdminStates_global.change_script,
    F.text == kc.buttons_admin_changes["change_general_script"],
)
async def change_general(message: Message, state: FSMContext):
    scenarios = await get_all_scenarios()
    if not scenarios:
        await message.answer("Ошибка при получении сценариев. Попробуйте позже.")
        return
    await message.answer("Собираю информацию...", reply_markup=kb.back_to_menu_kb())
    keyboard = kb.inline_scenario_selection_keyboard(scenarios)
    prompt_message = await message.answer(
        "Выберите общий сценарий для изменения.", reply_markup=keyboard
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates_global.change_script)


@admin_router.message(AdminStates_global.choose_edit_option)
async def handle_choose_edit_option(message: Message, state: FSMContext):
    if message.text == "Назад":
        scenarios = await get_all_scenarios()
        keyboard = kb.inline_scenario_selection_keyboard(scenarios)
        await message.answer(back_to_choice, reply_markup=kb.back_to_menu_kb())
        await message.answer(
            "Выберите общий сценарий для изменения.", reply_markup=keyboard
        )
        await state.set_state(AdminStates_global.change_script)
        return

    if message.text not in ["edit_message", "edit_time"]:
        await message.answer(
            "Сначала необходимо выбрать, что вы хотите отредактировать. Пожалуйста, нажмите на кнопку."
        )
        return

    match message.text:
        case "edit_message":
            await state.set_state(AdminStates_global.edit_script_message)
        case "edit_time":
            await state.set_state(AdminStates_global.edit_script_time)


@admin_router.callback_query(F.data.in_(["edit_message", "edit_time"]))
async def edit_choice_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    choice = callback_query.data
    await hf.edditing_message_or_time(callback_query, choice)
    match choice:
        case "edit_message":
            await state.set_state(AdminStates_global.edit_script_message)
        case "edit_time":
            await state.set_state(AdminStates_global.edit_script_time)


@admin_router.callback_query(
    AdminStates_global.change_script, F.data.startswith("change_scenario_")
)
async def handle_choose_scenario(callback_query: CallbackQuery, state: FSMContext):
    await hf.choose_general_scenario(callback_query, state)


@admin_router.message(AdminStates_changes.select_message)
async def handle_select_scenario_message(message: Message, state: FSMContext):
    if message.text == "Назад":
        scenarios = await get_all_scenarios()
        keyboard = kb.inline_scenario_selection_keyboard(scenarios)
        await message.answer(back_to_choice, reply_markup=kb.back_to_menu_kb())
        await message.answer(
            "Выберите общий сценарий для изменения.", reply_markup=keyboard
        )
        await state.set_state(AdminStates_global.change_script)
        return

    await hf.select_scenario_message(message, state)
    await state.set_state(AdminStates_global.choose_edit_option)


@admin_router.message(AdminStates_global.edit_script_message)
async def handle_edit_scenario_message(message: Message, state: FSMContext):
    if message.text == "Назад":
        scenarios = await get_all_scenarios()
        keyboard = kb.inline_scenario_selection_keyboard(scenarios)
        await message.answer(back_to_choice, reply_markup=kb.back_to_menu_kb())
        await message.answer(
            "Выберите общий сценарий для изменения.", reply_markup=keyboard
        )
        await state.set_state(AdminStates_global.change_script)
        return

    await hf.edit_scenario_message(message, state)


@admin_router.message(AdminStates_global.edit_script_time)
async def handle_edit_time(message: Message, state: FSMContext):
    if message.text == "Назад":
        scenarios = await get_all_scenarios()
        keyboard = kb.inline_scenario_selection_keyboard(scenarios)
        await message.answer(back_to_choice, reply_markup=kb.back_to_menu_kb())
        await message.answer(
            "Выберите общий сценарий для изменения.", reply_markup=keyboard
        )
        await state.set_state(AdminStates_global.change_script)
        return

    await hf.edit_scenario_time(message, state)


@admin_router.message(
    F.text == kc.buttons_yn["yes"], AdminStates_global.waiting_for_more_editing
)
async def handle_edit_more(message: Message, state: FSMContext):
    scenarios = await get_all_scenarios()
    keyboard = kb.inline_scenario_selection_keyboard(scenarios)
    await message.answer(back_to_choice, reply_markup=kb.back_to_menu_kb())
    await message.answer(
        "Выберите общий сценарий для изменения.", reply_markup=keyboard
    )
    await state.set_state(AdminStates_global.change_script)


@admin_router.message(
    F.text == kc.buttons_yn["no"], AdminStates_global.waiting_for_more_editing
)
async def handle_stop_editing(message: Message, state: FSMContext):
    await message.answer(choice_action, reply_markup=kb.changes_admin_kb())
    await state.set_state(AdminStates_global.menu)


@admin_router.message(
    AdminStates_global.find_patient,
    F.text == kc.buttons_admin_find["find_by_surname"],
)
async def find_by_surname(message: Message, state: FSMContext):
    prompt_message = await message.answer(
        "Введите фамилию по образцу: Иванова", reply_markup=kb.back_to_menu_kb()
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates_find.surname)


@admin_router.message(
    AdminStates_global.find_patient,
    F.text == kc.buttons_admin_find["find_by_phone"],
)
async def find_by_phone(message: Message, state: FSMContext):
    prompt_message = await message.answer(
        "Введите номер в формате +7XXXXXXXXXX", reply_markup=kb.back_to_menu_kb()
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates_find.telephone)


@admin_router.message(
    AdminStates_global.find_patient,
    F.text == kc.buttons_admin_find["find_by_doctor"],
)
async def find_by_doctor(message: Message, state: FSMContext):
    global prompt_message, all_doctors
    if all_doctors is None:
        await message.answer("Собираю информацию...", reply_markup=kb.back_to_menu_kb())
        all_doctors = await find_all_doctors()

    prompt_message = await message.answer(
        "Пациент какого врача вас интересует?",
        reply_markup=kb.inline_doctors_keyboard(all_doctors),
    )
    await state.update_data(prompt_message_id=prompt_message.message_id)
    await state.set_state(AdminStates_find.doctor_name_first)


@admin_router.callback_query(AdminStates_find.doctor_name_first)
async def information_by_doctor(query: CallbackQuery, state: FSMContext):
    await query.answer()
    doctor_id = int(query.data)
    global all_patients, prompt_message

    all_patients = await find_all_patients(doctor_id)
    data = await state.get_data()

    if all_patients:
        await hf.delete_previous_messages(
            query.message.bot, query.message.chat.id, data
        )
        # Удаление сообщения о врачах
        try:
            await query.message.delete()
        except Exception as e:
            logger.exception(f"Error deleting current message: {e}")

        prompt_message = await query.message.answer(
            "Какой именно пациент вас интересует?",
            reply_markup=kb.inline_patients_keyboard(all_patients, "doctors_name"),
        )
        await state.update_data(
            prompt_message_id=prompt_message.message_id, previous_message_ids=[]
        )
        await state.set_state(AdminStates_find.doctor_name_second)
    else:
        no_patients = await query.message.answer(
            "К сожалению, у данного врача нет пациентов. Попробуйте найти пациента по другому врачу или по "
            "фамилии/номеру телефона."
        )
        await state.update_data(
            prompt_message_id=no_patients.message_id,
            previous_message_ids=[no_patients.message_id],
        )


@admin_router.callback_query(AdminStates_find.doctor_name_second)
async def information_by_doctor_second(query: CallbackQuery, state: FSMContext):
    await query.answer()
    global all_patients, prompt_message
    patient_id = query.data

    if patient_id == "back_to_doctors":
        data = await state.get_data()
        await hf.delete_previous_messages(
            query.message.bot, query.message.chat.id, data
        )

        try:
            await query.message.delete()
        except Exception as e:
            logger.exception(f"Ошибка при удалении сообщения: {e}")

        await state.set_state(AdminStates_global.find_patient)
        await find_by_doctor(query.message, state)
        return

    patient_info = next(
        (
            p
            for p in all_patients["result"]["items"]
            if p["patient_id"] == int(patient_id)
        ),
        None,
    )

    if patient_info:
        data = await state.get_data()
        await hf.delete_previous_messages(
            query.message.bot, query.message.chat.id, data, exclude_prompt=True
        )

        response_message = hf.format_patient_info(patient_info)
        new_message = await query.message.answer(response_message)
        prompt_message = await query.message.answer(
            "Интересует ли какой-то пациент ещё? Выберите другого пациента или необходимое действие на клавиатуре."
        )

        await state.update_data(
            previous_message_ids=[new_message.message_id, prompt_message.message_id]
        )


@admin_router.message(AdminStates_find.surname)
async def information_by_last_name(message: Message, state: FSMContext):
    global all_patients
    information = message.text
    all_patients = await hf.find_information(message, state, information, "last_name")


@admin_router.message(AdminStates_find.telephone)
async def information_by_phone(message: Message, state: FSMContext):
    information = message.text
    await hf.find_information(message, state, information, "phone_number")
