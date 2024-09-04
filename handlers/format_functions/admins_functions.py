from aiogram import types
from aiogram.types import URLInputFile

import keyboards.admin_kb as kb

from database.constants_db import stage_number_to_name
from database.supabase_helpers import get_url
from aiogram.fsm.storage.base import StorageKey
from handlers.patient import switch_survey
from scheduler.sched_tasks import split_message_to_two_parts

from states.states_admin import (
    AdminStates_global,
    AdminStates_find,
    AdminStates_changes,
)

import logging
from database.admin_db import (
    get_info_patient_number_surname,
    get_all_scenarios,
    find_id_doctor,
)
from configuration.config_db import get_client
from configuration.config_bot import dp

import re
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.admin_db import (
    get_scenario_data,
    update_supabase,
    save_edited_message,
    save_edited_time,
)

supabase = get_client()
logger = logging.getLogger(__name__)


async def reset_information(state, message):
    data = await state.get_data()
    prompt_message_id = data.get("prompt_message_id")

    if prompt_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=prompt_message_id
            )
        except Exception as e:
            logger.exception(f"Ошибка при удалении собщений: {e}")


def format_patient_info(patient_info):
    stage = patient_info["stage"]
    name_stage = stage_number_to_name[stage]
    response_message = (
        f"Имя пациента: {patient_info['patient_name']} \n"
        f"Номер телефона пациента: {patient_info['patient_phone']}\n"
        f"Этап лечения пациента: {name_stage}\n"
    )
    if "doctor_name" in patient_info and patient_info["doctor_name"]:
        response_message += f"Имя врача: {patient_info['doctor_name']}\n"
    return response_message


def format_message(index, message):
    msg_type = message.get("type", "не установлено")
    content = message.get("content", "")
    url = message.get("url", "")
    time = message.get("time", "")
    match msg_type:
        case "text":
            formatted_message = f"{index}. {content}"
        case "image":
            formatted_message = f"{index}. Изображение🖼️: {url}"
        case "video":
            formatted_message = f"{index}. Видео🎦: {url}"
        case "link":
            formatted_message = f"{index}. Ссылка🔗: {url}"
        case "text image":
            formatted_message = f"{index}. {content} (Изображение к сообщению🖼️: {url})"
        case "text video":
            formatted_message = f"{index}. {content} (Видео к сообщению🎦: {url})"
        case "survey":
            formatted_message = f"{index}. Опрос: \n{content}"
        case _:
            formatted_message = f"{index}. {content}"

    if time and time != "0":
        formatted_message += f" (Время отправки: {time})"

    return formatted_message


def format_scenarios(current_part, scenarios, max_message_length=4096):
    response_parts = []

    for scenario in scenarios:
        unique_messages = {msg["id"]: msg for msg in scenario["messages"]}
        sorted_messages = sorted(unique_messages.values(), key=lambda x: x["id"])

        for i, message in enumerate(sorted_messages):
            formatted_message = format_message(i + 1, message)

            # Каждое сообщение добавляется как отдельная часть
            response_parts.append(current_part + formatted_message)

            # Очистка current_part для следующего сообщения
            current_part = ""

    return response_parts


async def delete_previous_messages(bot, chat_id, data, exclude_prompt=False):
    message_ids = data.get("previous_message_ids", [])
    if exclude_prompt:
        prompt_message_id = data.get("prompt_message_id")
        message_ids = [msg_id for msg_id in message_ids if msg_id != prompt_message_id]

    for message_id in message_ids:
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception as e:
            logger.exception(f"Ошибка при удалении сообщения {message_id}: {e}")


async def find_information(message, state, info, by_what):
    all_patients = await get_info_patient_number_surname(info, by_what)
    if all_patients is not None:
        information = all_patients["result"]["items"]
        if len(information) > 1:
            await message.answer(
                "Какой именно пациент вас интересует?",
                reply_markup=kb.inline_patients_keyboard(all_patients, "surname"),
            )
            await state.set_state(AdminStates_find.doctor_name_second)
            return all_patients
        else:
            patient_info = information[0]
            response_message = format_patient_info(patient_info)

            await message.answer("Вот что я сумел найти: ")
            await message.answer(response_message)
            await message.answer(
                "Что ещё хотите сделать?", reply_markup=kb.find_admin_kb()
            )
            await state.set_state(AdminStates_global.find_patient)
    else:
        if by_what == "phone_number":
            await message.answer(
                "К сожалению произошла ошибка. Возможно я не смог найти какие-то данные. Попробуйте снова ввести "
                "номер телефона"
            )
            await state.set_state(AdminStates_find.telephone)
        else:
            await message.answer(
                "К сожалению произошла ошибка. Возможно я не смог найти какие-то данные. Попробуйте снова ввести "
                "фамилию"
            )
            await state.set_state(AdminStates_find.surname)


def replace_placeholders(content, first_name, last_name):
    # Заменяем плейсхолдеры {first_name} и {last_name}
    content = content.replace("{first_name}", first_name).replace(
        "{last_name}", last_name
    )
    content = content.replace("/n", "\n")

    return content


async def send_message_list(message: types.Message, state: FSMContext):
    data = await state.get_data()
    messages = data.get("messages", [])
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    if not messages:
        await message.answer("В данном сценарии нет сообщений.")
        return

    # Форматируем сообщения с использованием format_scenarios
    formatted_messages = format_scenarios("", [{"messages": messages}])

    # Заменяем плейсхолдеры и переводим \n в переносы строк в каждом сообщении
    formatted_messages = [
        replace_placeholders(part, first_name, last_name).replace("\\n", "\n")
        for part in formatted_messages
    ]

    # Отправляем каждую часть отформатированных сообщений
    for part in formatted_messages:
        await message.answer(part)

    # Запрашиваем ввод номера сообщения для отправки
    await message.answer("Введите номер сообщения для отправки:")


async def process_phone_number(message: types.Message, state: FSMContext, back_to):
    if message.text == "Назад":
        await back_to(message, state)
        return

    phone_number = message.text

    if (
        not phone_number.startswith("+7")
        or len(phone_number) != 12
        or not phone_number[1:].isdigit()
    ):
        await message.answer(
            "Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX."
        )
        return

    try:
        client_response = (
            supabase.table("clients")
            .select("id, tg_id", "stage", "first_name", "last_name")
            .eq("phone_number", phone_number)
            .execute()
        )
        client_data = client_response.data

        if not client_data:
            await message.answer(
                "Пациент с таким номером телефона не найден. Пожалуйста, введите номер телефона "
                "авторизованного клиента в формате +7XXXXXXXXXX."
            )
            return

        client = client_data[0]
        tg_id = client["tg_id"]
        stage = client.get("stage", "Неизвестен")
        name_stage = stage_number_to_name[stage]
        first_name = client.get("first_name")
        last_name = client.get("last_name")
        # Отправляем сообщение о найденном клиенте и его текущем этапе
        await message.answer(
            f"Клиент найден✅\nКлиент: {first_name} {last_name}\nЭтап клиента: {name_stage}\n\n",
            reply_markup=kb.back_to_messages_kb(),
        )

        scenarios = await get_all_scenarios()
        stage_buttons = kb.inline_scenario_selection_keyboard(scenarios)

        await message.answer(
            "Выберите сценарий из которого вы хотите отправить сообщение:",
            reply_markup=stage_buttons,
        )

        # Сохраняем данные клиента в состоянии
        await state.update_data(tg_id=tg_id, first_name=first_name, last_name=last_name)
        await state.set_state(AdminStates_global.waiting_for_stage)

    except Exception as e:
        logger.exception(f"Ошибка при обработке номера телефона: {e}")
        await message.answer(
            "Произошла ошибка при обработке номера телефона. Попробуйте снова.",
            reply_markup=kb.back_to_messages_kb(),
        )


async def process_message_number(
    message: types.Message, state: FSMContext, back_to, id
):
    if message.text == "Назад":
        await back_to(message, state)
        return

    message_number = int(message.text)
    data = await state.get_data()
    messages = data.get("messages", [])
    tg_id = data.get("tg_id")
    bot = message.bot
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    if not (message.text.isdigit() and 1 <= message_number <= len(messages)):
        await message.answer(
            "Сообщение с указанным номером не существует. Пожалуйста, введите корректный номер сообщения."
        )
        return

    message_to_send = messages[message_number - 1]
    content = replace_placeholders(
        message_to_send.get("content", ""), first_name, last_name
    ).replace("/n", "\n")

    max_message_length = 4096
    max_caption_length = 1024

    try:
        msg_type = message_to_send.get("type", "")
        match msg_type:
            case "text":
                # Разбиваем сообщение на части, если оно слишком длинное
                parts = split_message_to_two_parts(content, max_message_length)
                for part in parts:
                    await bot.send_message(tg_id, part)
            case "video":
                video = message_to_send["url"]
                if len(video) == 0:
                    id_doctor = await find_id_doctor(tg_id)
                    format_video = f"{id}.{message_number}.{id_doctor['doctor_id']}"
                    video = URLInputFile(await get_url(format_video))
                await bot.send_video(tg_id, video)
            case "text video":
                video = URLInputFile(message_to_send["url"])
                if len(content) > max_caption_length:
                    # Обрезаем caption и отправляем оставшийся текст отдельно
                    caption_part = content[:max_caption_length]
                    remaining_content = content[max_caption_length:]
                    await bot.send_video(tg_id, video, caption=caption_part)
                    await bot.send_message(tg_id, remaining_content)
                else:
                    await bot.send_video(tg_id, video, caption=content)
            case "link":
                await bot.send_message(tg_id, message_to_send["url"])
            case "text image":
                photo = URLInputFile(message_to_send["url"])
                if len(content) > max_caption_length:
                    # Обрезаем caption и отправляем оставшийся текст отдельно
                    caption_part = content[:max_caption_length]
                    remaining_content = content[max_caption_length:]
                    await bot.send_photo(tg_id, photo, caption=caption_part)
                    await bot.send_message(tg_id, remaining_content)
                else:
                    await bot.send_photo(tg_id, photo, caption=content)
            case "text link":
                if len(content) > max_caption_length:
                    # Обрезаем caption и отправляем оставшийся текст отдельно
                    caption_part = content[:max_caption_length]
                    remaining_content = content[max_caption_length:]
                    await bot.send_message(
                        tg_id, f'{caption_part}\n{message_to_send["url"]}'
                    )
                    await bot.send_message(tg_id, remaining_content)
                else:
                    await bot.send_message(
                        tg_id, f'{content}\n{message_to_send["url"]}'
                    )
            case "survey":
                id_survey = message_to_send.get("id_survey")
                state_with = FSMContext(
                    storage=dp.storage,
                    key=StorageKey(chat_id=tg_id, user_id=tg_id, bot_id=bot.id),
                )
                await switch_survey(state_with, tg_id, id_survey)
            case _:
                await message.answer(
                    "Неизвестный тип сообщения. Пожалуйста, выберите правильное сообщение."
                )

        await message.answer("Сообщение успешно отправлено!")

        keyboard = kb.yes_no_keyboard()
        await message.answer("Отправить ещё сообщения?", reply_markup=keyboard)
        await state.set_state(AdminStates_global.waiting_for_more_messages)

    except Exception as e:
        logger.exception(f"Ошибка при отправке сообщения: {e}")
        await message.answer(
            "Произошла ошибка при отправке сообщения. Попробуйте снова.",
            reply_markup=kb.back_to_messages_kb(),
        )


async def choose_general_scenario(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    scenario_id = int(callback_query.data.split("_")[-1])
    scenario_data = await get_scenario_data(scenario_id)
    scenario_name = scenario_data.get("name_stage", "Без названия")

    if not scenario_data or "messages" not in scenario_data:
        await callback_query.message.answer(
            "Ошибка при получении данных сценария. Попробуйте позже."
        )
        return

    response_text = format_scenarios("", [scenario_data])
    for part in response_text:
        await callback_query.message.answer(part)

    await callback_query.message.answer(
        "Напишите номер сообщения, которое вы хотите изменить.",
        reply_markup=kb.back_to_messages_kb(),
    )
    await state.update_data(
        scenario_id=scenario_id, unique_messages=scenario_data["messages"]
    )
    await state.set_state(AdminStates_changes.select_message)


async def select_scenario_message(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer(
            "Неверный формат выбора. Пожалуйста, укажите номер сообщения.",
            reply_markup=kb.back_to_messages_kb(),
        )
        return

    try:
        message_index = int(message.text.split(".")[0]) - 1
    except (ValueError, IndexError):
        logger.error(f"Ошибка при считывании номера сообщения")
        await message.answer(
            "Неверный формат выбора. Пожалуйста, укажите номер сообщения.",
            reply_markup=kb.back_to_messages_kb(),
        )
        return

    data = await state.get_data()
    scenario_id = data.get("scenario_id")
    unique_messages = data.get("unique_messages")

    if not scenario_id or not unique_messages:
        await message.answer(
            "Ошибка при получении данных сценария.",
            reply_markup=kb.back_to_messages_kb(),
        )
        return

    if message_index < 0 or message_index >= len(unique_messages):
        await message.answer(
            "Сообщение с указанным номером не существует. Пожалуйста, введите корректный номер сообщения.",
            reply_markup=kb.back_to_messages_kb(),
        )
        # Сбрасываем состояние, чтобы администратор мог ввести номер сообщения заново
        await state.finish()
        return

    selected_message = unique_messages[message_index]

    edit_prompt = f"Вы выбрали сообщение для редактирования: \n{format_message(message_index + 1, selected_message)}"
    await message.answer(edit_prompt, reply_markup=kb.back_to_messages_kb())
    await message.answer(f"Время отправки сообщения: {selected_message['time']}")
    await message.answer(
        "Что вы хотите отредактировать?", reply_markup=kb.edit_global_choice_keyboard()
    )

    # Обновляем данные состояния и устанавливаем состояние выбора редактирования
    await state.update_data(
        selected_message_id=selected_message["id"],
        selected_message_index=message_index,
        scenario_id=scenario_id,
        unique_messages=unique_messages,
    )
    await state.set_state(AdminStates_global.choose_edit_option)


async def edditing_message_or_time(query, choice):
    choice = query.data
    await query.message.delete()
    match choice:
        case "edit_message":
            await query.message.answer(
                "Теперь начните вводить текст или вставьте ссылку на видео/изображение",
                reply_markup=kb.back_to_messages_kb(),
            )
        case "edit_time":
            await query.message.answer(
                "Теперь введите новое время в формате: (+/-)2 10:00",
                reply_markup=kb.back_to_messages_kb(),
            )
            await query.message.answer(
                "Где:\n +/- - обозначение после поцедуры и до соотвественно.\n2 - количество суток. Если отправка в тот "
                "же день, что и процедура, напишите 0\n10:00 - точное время отправки.\nЕсли какой-то из параметров "
                "отсутствует писать что-либо не обязательно."
            )


async def edit_scenario_message(message: Message, state: FSMContext):
    data = await state.get_data()
    scenario_id = data.get("scenario_id")
    selected_message_id = data.get("selected_message_id")
    unique_messages = data.get("unique_messages")

    # Найдем текущее сообщение по ID
    current_message = next(
        (msg for msg in unique_messages if msg["id"] == selected_message_id), None
    )
    if not current_message:
        await message.answer(
            "Сообщение не найдено.", reply_markup=kb.back_to_messages_kb()
        )
        return

    # Сохраняем оригинальный тип и URL сообщения
    original_type = current_message.get("type", "text")
    original_url = current_message.get("url")

    if message.photo:
        # Обработка фото
        new_content = message.photo[-1].file_id
        content_type = "text image"
        new_url = original_url  # Сохраняем оригинальный URL, если это фото
    else:
        # Обработка текста
        text = message.text.strip()
        url, extracted_content = extract_url_and_content(text)

        if url:
            # Если в тексте есть URL
            new_url = url
            if original_type in ["text image", "text video"]:
                # Если оригинальный тип был "text image" или "text video", сохраняем его
                new_content = current_message.get("content", "")
                content_type = original_type
            else:
                # Определяем новый тип контента на основе URL
                new_content = extracted_content
                content_type = determine_content_type(new_url, new_content)
        else:
            # Если URL нет, просто обновляем контент
            new_url = original_url
            new_content = extracted_content
            content_type = original_type  # Сохраняем оригинальный тип

    # Обновляем сообщение
    current_message["content"] = new_content
    current_message["type"] = content_type
    if content_type in ["text image", "text video", "text link"]:
        current_message["url"] = new_url

    # Сохраняем изменения
    await save_edited_message(scenario_id, unique_messages)
    await message.answer("Сообщение успешно изменено.")
    await message.answer(
        "Хотите ли вы продолжить редактирование?", reply_markup=kb.yes_no_keyboard()
    )
    await state.set_state(AdminStates_global.waiting_for_more_editing)


async def edit_scenario_time(message: Message, state: FSMContext):
    try:
        new_time = message.text.strip()

        # Обновленное регулярное выражение для проверки времени
        if not re.match(r"^[+-]?\d+ \d{2}:\d{2}$", new_time):
            raise ValueError(
                "Неверный формат времени. Введите время в формате +36 13:00 или -36 10:00."
            )

        data = await state.get_data()
        scenario_id = data.get("scenario_id")
        selected_message_id = data.get("selected_message_id")
        unique_messages = data.get("unique_messages")

        # Найдем текущее сообщение по ID
        current_message = next(
            (msg for msg in unique_messages if msg["id"] == selected_message_id), None
        )
        if not current_message:
            raise ValueError("Сообщение не найдено.")

        # Обновляем время в сообщении
        current_message["time"] = new_time
        await save_edited_time(
            scenario_id, selected_message_id, new_time, unique_messages
        )

        await message.answer("Время отправки сообщения успешно изменено.")
        await message.answer(
            "Хотите ли вы продолжить редактирование?", reply_markup=kb.yes_no_keyboard()
        )
        await state.set_state(AdminStates_global.waiting_for_more_editing)

    except ValueError as e:
        await message.answer(str(e), reply_markup=kb.back_to_messages_kb())


def determine_content_type(url, content):
    """Определение типа контента на основе URL и текста."""
    if url and content:
        if re.match(r"https?:\/\/.*\.(jpg|jpeg|png|gif)", url, re.IGNORECASE):
            return "text image"
        elif re.match(r"https?:\/\/.*\.(mp4|avi|mov|m4v|webm|flv)", url, re.IGNORECASE):
            return "text video"
        elif re.match(r"https?:\/\/", url, re.IGNORECASE):
            return "text link"
    elif url:
        if re.match(r"https?:\/\/.*\.(jpg|jpeg|png|gif)", url, re.IGNORECASE):
            return "image"
        elif re.match(r"https?:\/\/.*\.(mp4|avi|mov|m4v|webm|flv)", url, re.IGNORECASE):
            return "video"
        elif re.match(r"https?:\/\/", url, re.IGNORECASE):
            return "link"
    elif content:
        return "text"

    return "text"  # Default to text if nothing else matches


def extract_url_and_content(text):
    """Извлекает URL и содержание из текста, если они есть."""
    url_pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    url_match = url_pattern.search(text)

    if url_match:
        url = url_match.group(0)
        content = text.replace(url, "").strip()
        return url, content
    else:
        return None, text.strip()


async def changin_scenario_in_bd(scenarios, number, editing_text, by_what):
    for scenario in scenarios["result"]["items"]:
        try:
            number = int(number)
        except ValueError:
            logger.error(f"Неправильный формат номера сообщения")
            return {"status": "error", "message": "Invalid message number"}

        message = next(
            (msg for msg in scenario["messages"] if msg["id"] == number), None
        )
        if message:
            match by_what:
                case "edit_message":
                    url, content = extract_url_and_content(editing_text)
                    message["content"] = content
                    if url:
                        message["url"] = url
                    else:
                        message.pop("url", None)
                    message["type"] = determine_content_type(url, content)
                case "edit_time":
                    # Разделяем введённое время на две части
                    time_parts = editing_text.split()

                    try:
                        # Сохраняем знак и преобразуем значение с учетом знака
                        first_time = time_parts[0]
                        if first_time[0] in ["+", "-"]:
                            sign = first_time[0]
                            number_part = int(first_time[1:]) * 24
                            first_time = f"{sign}{number_part}"
                        else:
                            first_time = str(int(first_time) * 24)

                        second_time = time_parts[1] if len(time_parts) > 1 else "0"
                        message["time"] = f"{first_time} {second_time}"
                    except (ValueError, IndexError):
                        logger.error(f"Ошибка в формате времени")
                        return {"status": "error", "message": "Invalid time format"}
            data_to_update = {
                "messages": scenario["messages"],
                "name_stage": scenario.get("name_stage", ""),
                "procedures": scenario.get("procedures", []),
            }

            try:
                result = await update_supabase(
                    "users_scenarios",
                    {"scenarios": data_to_update},
                    scenario["scenario_id"],
                )
                # Проверяем результат обновления данных
                if result.get("status") == "success":
                    return {"status": "success"}
                else:
                    logger.error(f"Ошибка при обновлении сценария")
                    return {"status": "error", "message": "Failed to update scenario"}
            except Exception as e:
                logger.error(f"Ошибка при запросе к Supabase: {e}")
                return {"status": "error", "message": str(e)}

    logger.error(f"Сообщение не было найдено")
    return {"status": "error", "message": "Message not found"}
