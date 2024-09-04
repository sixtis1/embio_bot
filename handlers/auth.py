import asyncio
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType
import logging
from handlers.format_functions.auth_crm_functions import (
    get_user_data,
    get_sotr_data,
    find_first_stage_trigger,
    authenticate_patient,
    authenticate_doctor,
)
from states.auth_states import AuthStates
from states.states_doctor import DoctorStates
from states.states_patient import PatientStates
from handlers.patient import handle_patient_command, survey_info
from handlers.doctor import handler_doctor_command
from keyboards.auth_kb import get_phone_keyboard
from states.states_admin import AdminStates_global
from handlers.admin import command_admin
from database.auth_db import (
    save_client_data,
    save_doctor_data,
    get_client,
    check_if_admin,
)

auth_router = Router()
processing_message = "Обработка запроса, пожалуйста подождите..."

logger = logging.getLogger(__name__)


@auth_router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    chat_id = message.chat.id

    # Проверка, является ли пользователь администратором
    admin_check_response = await check_if_admin(chat_id)
    if admin_check_response:
        # если является, его сразу перекидывает в admin без авторизации

        await state.set_state(AdminStates_global.menu)
        await command_admin(message, state)
        return

    keyboard = get_phone_keyboard()
    await message.answer(
        "Добро пожаловать! Я Ассистент ЭмБио, готов помочь на пути лечения :)\nПожалуйста, нажмите кнопку ниже, "
        "чтобы поделиться своим номером телефона, или введите номер вручную в формате +7XXXXXXXXXX.",
        reply_markup=keyboard,
    )
    await state.set_state(AuthStates.waiting_for_phone)


@auth_router.message(F.content_type == ContentType.CONTACT)
async def process_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    phone = contact.phone_number
    processing_msg = await message.answer(processing_message)
    await process_phone_number(message, state, phone, processing_msg)


@auth_router.message(AuthStates.waiting_for_phone)
async def process_phone_input(message: types.Message, state: FSMContext):
    phone = message.text
    processing_msg = await message.answer(processing_message)
    await process_phone_number(message, state, phone, processing_msg)


async def process_phone_number(
    message: types.Message, state: FSMContext, phone=None, processing_msg=None
):
    try:
        response = await get_user_data(phone)
        if response.get("result", {}).get("code") == 0:
            await asyncio.sleep(3)
            await processing_msg.delete()
            await message.answer(
                "Номер телефона был найден. Пожалуйста, введите последние 4 цифры вашего паспорта."
            )
            await state.update_data(
                # сохраняю телефон пациента и tg_id в состояние
                role="patient",
                phone=phone,
                tg_id=message.from_user.id,
            )
            await state.set_state(AuthStates.waiting_for_additional_info)
        else:
            response = await get_sotr_data(phone)
            if response.get("result", {}).get("code") == 0:
                await asyncio.sleep(3)
                await processing_msg.delete()
                sotr_info = response["result"]["item"]
                if sotr_info["dolj"]:
                    # сохраняю телефон врача и tg_id в состояние
                    await state.update_data(
                        role="doctor", phone=phone, tg_id=message.from_user.id
                    )
                    await message.answer(
                        "Номер телефона был найден. Пожалуйста, введите ваш ID врача."
                    )
                    await state.set_state(AuthStates.waiting_for_additional_info)
                else:
                    await message.answer(
                        "Роль не определена. Пожалуйста, введите номер телефона в формате +7XXXXXXXXXX."
                    )
                    await state.set_state(AuthStates.waiting_for_phone)
            else:
                await asyncio.sleep(3)
                await processing_msg.delete()
                await message.answer(
                    "Номер телефона не был найден на сервере. Пожалуйста, введите номер, который привязан к учетной "
                    "записи в формате +7XXXXXXXXXX."
                )
                await state.set_state(AuthStates.waiting_for_phone)
    except Exception:
        if processing_msg:
            await processing_msg.delete()
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")


@auth_router.message(AuthStates.waiting_for_additional_info)
async def process_additional_info(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    phone = user_data.get("phone")
    additional_info = message.text

    authenticated = False
    match user_data.get("role"):
        case "patient":
            authenticated = await authenticate_patient(phone, additional_info, state)
            if authenticated:
                user_info = await state.get_data()
                client_id = user_info.get("id_crm")
                tg_id = user_info.get("tg_id")  # получаю tg_id из состояния

                # Найти числовое значение первого этапа
                if client_id:
                    stage_number = await find_first_stage_trigger(client_id)
                else:
                    stage_number = None

                # Сохранить информацию о пациенте
                await save_client_data(
                    tg_id,
                    user_info["name"].split()[1],
                    user_info["name"].split()[0],
                    user_info.get("passport"),
                    phone,
                    client_id,
                    stage=stage_number,
                )

                # Отправка сообщения об успешной авторизации
                await message.answer("Успешная авторизация!")

        case "doctor":
            authenticated = await authenticate_doctor(phone, additional_info, state)
            if authenticated:
                user_info = await state.get_data()
                tg_id = user_info.get("tg_id")  # получаю tg_id из состояния
                await save_doctor_data(
                    user_info["name"].split()[1],
                    user_info["name"].split()[0],
                    user_info.get("specialty"),
                    phone,
                    user_info.get("id_crm"),
                    tg_id,
                )

                # Отправка сообщения об успешной авторизации
                await message.answer("Успешная авторизация!")

    if authenticated:
        name = (await state.get_data()).get("name")
        match user_data.get("role"):
            case "patient":
                await state.set_state(PatientStates.menu)
                await handle_patient_command(message, state)
            case "doctor":
                await state.set_state(DoctorStates.menu)
                await handler_doctor_command(message, state)
    else:
        await message.answer("Неверные данные. Пожалуйста, попробуйте снова.")
