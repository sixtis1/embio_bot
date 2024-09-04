import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import types
from aiogram.types import Message, Chat, Contact
from handlers.auth import (
    start_command,
    process_contact,
    processing_message,
    process_phone_input,
    process_phone_number,
    process_additional_info,
)
from states.auth_states import AuthStates
from keyboards.auth_kb import get_phone_keyboard


@pytest.mark.asyncio
async def test_start_command():
    # тест проверяет, что команда /start запускает правильное приветственное сообщение и клавиатуру для ввода номера
    # телефона
    message = AsyncMock(spec=Message)
    state = AsyncMock()
    chat = AsyncMock(spec=Chat)
    chat.id = 12345678
    message.chat = chat
    message.answer = AsyncMock()
    keyboard = get_phone_keyboard()

    with patch("keyboards.auth_kb.get_phone_keyboard", return_value=keyboard):
        await start_command(message, state)

        # проверяем, что метод message.answer был вызван с правильными аргументами
        message.answer.assert_called_once_with(
            "Добро пожаловать! Я Ассистент ЭмБио, готов помочь на пути лечения :)\nПожалуйста, нажмите кнопку ниже, "
            "чтобы поделиться своим номером телефона, или введите номер вручную в формате +7XXXXXXXXXX.",
            reply_markup=keyboard,
        )


@pytest.mark.asyncio
async def test_process_contact():
    # тест проверяет, что при получении контакта от пользователя, запускается процесс обработки номера телефона
    message = AsyncMock(spec=Message)
    contact = MagicMock(spec=Contact)
    state = AsyncMock()
    contact.phone_number = "+71234567890"
    message.contact = contact
    message.answer = AsyncMock()

    with patch(
        "handlers.auth.process_phone_number", new=AsyncMock()
    ) as mocked_process_phone_number:
        processing_msg = AsyncMock()
        message.answer.return_value = processing_msg

        await process_contact(message, state)

        # проверяем, что отправляется сообщение об обработке и вызывается функция обработки номера телефона
        message.answer.assert_called_once_with(processing_message)
        mocked_process_phone_number.assert_called_once_with(
            message, state, "+71234567890", processing_msg
        )


@pytest.mark.asyncio
async def test_process_phone_input():
    # тест проверяет, что при вводе номера телефона пользователем, запускается процесс обработки номера телефона
    message = AsyncMock(spec=Message)
    state = AsyncMock()
    phone_number = "+71234567890"
    message.text = phone_number
    message.answer = AsyncMock()
    expected_processing_message = "Обработка запроса, пожалуйста подождите..."

    with patch(
        "handlers.auth.process_phone_number", new=AsyncMock()
    ) as mocked_process_phone_number:
        processing_msg = AsyncMock()
        message.answer.return_value = processing_msg

        await process_phone_input(message, state)

        # проверяем, что отправляется сообщение об обработке и вызывается функция обработки номера телефона
        message.answer.assert_called_once_with(expected_processing_message)
        mocked_process_phone_number.assert_called_once_with(
            message, state, phone_number, processing_msg
        )


@pytest.mark.asyncio
async def test_process_phone_number_role_not_found():
    # тест проверяет, что если номер телефона найден в базе данных, но роль не определена, пользователю предлагается ввести номер снова
    message = AsyncMock(spec=Message)
    state = AsyncMock()
    phone = "+71234567890"
    processing_msg = AsyncMock()
    message.answer = AsyncMock()
    user_data_response = {"result": {"code": 1}}  # Номер не найден
    sotr_data_response = {
        "result": {"code": 0, "item": {"dolj": "неизвестно"}}
    }  # Роль не определена

    with patch(
        "handlers.auth.get_user_data", new=AsyncMock(return_value=user_data_response)
    ):
        with patch(
            "handlers.auth.get_sotr_data",
            new=AsyncMock(return_value=sotr_data_response),
        ):
            await process_phone_number(message, state, phone, processing_msg)

            # Проверяем, что сообщение об обработке удаляется и пользователю предлагается ввести номер снова
            processing_msg.delete.assert_called_once()
            message.answer.assert_called_once_with(
                "Роль не определена. Пожалуйста, введите номер телефона в формате +7XXXXXXXXXX."
            )
            state.set_state.assert_called_once_with(AuthStates.waiting_for_phone)


@pytest.mark.asyncio
async def test_process_phone_number_sotr_not_found():
    # тест проверяет, что если номер телефона не найден ни в одной базе данных, пользователю предлагается ввести
    # номер снова
    message = AsyncMock(spec=Message)
    state = AsyncMock()
    phone = "+71234567890"
    processing_msg = AsyncMock()
    message.answer = AsyncMock()
    user_data_response = {"result": {"code": 1}}
    sotr_data_response = {"result": {"code": 1}}

    with patch(
        "handlers.auth.get_user_data", new=AsyncMock(return_value=user_data_response)
    ):
        with patch(
            "handlers.auth.get_sotr_data",
            new=AsyncMock(return_value=sotr_data_response),
        ):
            await process_phone_number(message, state, phone, processing_msg)

            # проверяем, что сообщение об обработке удаляется и пользователю предлагается ввести номер снова
            processing_msg.delete.assert_called_once()
            message.answer.assert_called_once_with(
                "Номер телефона не был найден на сервере. Пожалуйста, введите номер, который привязан к учетной "
                "записи в формате +7XXXXXXXXXX."
            )
            state.set_state.assert_called_once_with(AuthStates.waiting_for_phone)


@pytest.mark.asyncio
async def test_process_phone_number_error():
    # тест проверяет, что если при обработке номера телефона возникает ошибка, пользователю выводится сообщение об
    # ошибке
    message = AsyncMock(spec=Message)
    state = AsyncMock()
    phone = "+71234567890"
    processing_msg = AsyncMock()
    message.answer = AsyncMock()

    with patch("handlers.auth.get_user_data", new=AsyncMock(side_effect=Exception)):
        await process_phone_number(message, state, phone, processing_msg)

        # проверяем, что сообщение об обработке удаляется и пользователю выводится сообщение об ошибке
        processing_msg.delete.assert_called_once()
        message.answer.assert_called_once_with(
            "Произошла ошибка. Пожалуйста, попробуйте снова."
        )
