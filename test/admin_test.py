from handlers.format_functions.admins_functions import (
    format_message,
    format_scenarios,
    delete_previous_messages,
    find_information,
    process_phone_number,
)
import pytest
from unittest.mock import AsyncMock, patch, call
from states.states_admin import AdminStates_find, AdminStates_global
import keyboards.admin_kb as kb


@pytest.mark.parametrize(
    "message_id, message, expected_result",
    [
        # Тестирование текстового сообщения
        (
            1,
            {
                "type": "text",
                "content": "Простое сообщение",
                "url": "",
                "time": "10:00",
            },
            "1. Простое сообщение (Время отправки: 10:00)",
        ),
        # Тестирование изображения
        (
            2,
            {
                "type": "image",
                "content": "",
                "url": "http://example.com/image.jpg",
                "time": "10:00",
            },
            "2. Изображение🖼️: http://example.com/image.jpg (Время отправки: 10:00)",
        ),
        # Тестирование видео
        (
            3,
            {
                "type": "video",
                "content": "",
                "url": "http://example.com/video.mp4",
                "time": "10:00",
            },
            "3. Видео🎦: http://example.com/video.mp4 (Время отправки: 10:00)",
        ),
        # Тестирование ссылки
        (
            4,
            {
                "type": "link",
                "content": "",
                "url": "http://example.com",
                "time": "10:00",
            },
            "4. Ссылка🔗: http://example.com (Время отправки: 10:00)",
        ),
        # Тестирование текстового сообщения с изображением
        (
            5,
            {
                "type": "text image",
                "content": "Сообщение с изображением",
                "url": "http://example.com/image.jpg",
                "time": "10:00",
            },
            "5. Сообщение с изображением (Изображение к сообщению🖼️: http://example.com/image.jpg) (Время отправки: 10:00)",
        ),
        # Тестирование текстового сообщения с видео
        (
            6,
            {
                "type": "text video",
                "content": "Сообщение с видео",
                "url": "http://example.com/video.mp4",
                "time": "10:00",
            },
            "6. Сообщение с видео (Видео к сообщению🎦: http://example.com/video.mp4) (Время отправки: 10:00)",
        ),
        # Тестирование сообщения с временем
        (
            8,
            {
                "type": "text",
                "content": "Сообщение с временем",
                "url": "",
                "time": "15:30",
            },
            "8. Сообщение с временем (Время отправки: 15:30)",
        ),
    ],
)
def test_format_message(message_id, message, expected_result):
    """
    Тестирует функцию format_message:
    - Проверка различных типов сообщений и их форматирования.
    """
    result = format_message(message_id, message)
    assert result == expected_result


def test_format_scenarios_single_message():
    """Тестирует форматирование одного сообщения"""
    current_part = ""
    scenarios = [
        {
            "messages": [
                {"id": 1, "type": "text", "content": "Message 1", "url": "", "time": ""}
            ]
        }
    ]
    expected_result = ["1. Message 1"]
    result = format_scenarios(current_part, scenarios)
    assert result == expected_result


def test_format_scenarios_large_message_split():
    """Тестирует форматирование длинных сообщений с разбиением"""
    current_part = ""
    scenarios = [
        {
            "messages": [
                {"id": 1, "type": "text", "content": "A" * 4090, "url": "", "time": ""},
                {"id": 2, "type": "text", "content": "B" * 4090, "url": "", "time": ""},
            ]
        }
    ]
    expected_result = ["1. " + "A" * 4090, "2. " + "B" * 4090]
    result = format_scenarios(current_part, scenarios, max_message_length=4096)
    assert result == expected_result


@pytest.mark.asyncio
async def test_delete_previous_messages_no_exclusions():
    """Тестирует удаление предыдущих сообщений без исключений"""
    bot = AsyncMock()
    chat_id = 123
    data = {"previous_message_ids": [1, 2, 3]}
    await delete_previous_messages(bot, chat_id, data)
    calls = [call(chat_id, 1), call(chat_id, 2), call(chat_id, 3)]
    bot.delete_message.assert_has_awaits(calls)


@pytest.mark.asyncio
async def test_delete_previous_messages_with_error_handling():
    """Тестирует удаление сообщений с обработкой исключений"""
    bot = AsyncMock()
    bot.delete_message.side_effect = [
        Exception("Test exception"),
        Exception("Test exception"),
    ]
    chat_id = 123
    data = {"previous_message_ids": [1, 2]}
    with patch("handlers.format_functions.admins_functions.logger") as mock_logger:
        await delete_previous_messages(bot, chat_id, data)
        expected_calls = [call(chat_id, 1), call(chat_id, 2)]
        bot.delete_message.assert_has_awaits(expected_calls)
        expected_log_calls = [
            call("Ошибка при удалении сообщения 1: Test exception"),
            call("Ошибка при удалении сообщения 2: Test exception"),
        ]
        mock_logger.exception.assert_has_calls(expected_log_calls)


@pytest.mark.asyncio
async def test_find_information_multiple_patients():
    """Тестирует поиск информации с несколькими пациентами"""
    message = AsyncMock()
    state = AsyncMock()
    info = "some_info"
    by_what = "surname"
    all_patients = {
        "result": {
            "items": [
                {
                    "patient_name": "John Doe",
                    "patient_phone": "1234567890",
                    "stage": "Stage 1",
                    "doctor_name": "Dr. Smith",
                },
                {
                    "patient_name": "Jane Doe",
                    "patient_phone": "0987654321",
                    "stage": "Stage 2",
                    "doctor_name": "Dr. Jones",
                },
            ]
        }
    }
    with patch(
        "handlers.format_functions.admins_functions.get_info_patient_number_surname",
        return_value=all_patients,
    ) as mock_get_info:
        with patch(
            "handlers.format_functions.admins_functions.kb.inline_patients_keyboard"
        ) as mock_keyboard:
            result = await find_information(message, state, info, by_what)
            mock_get_info.assert_called_once_with(info, by_what)
            mock_keyboard.assert_called_once_with(all_patients, "surname")
            state.set_state.assert_called_once_with(AdminStates_find.doctor_name_second)
            assert result == all_patients


@pytest.mark.asyncio
async def test_process_phone_number_invalid_format():
    """Тестирует случай в process_phone_number с неверным форматом номера телефона"""
    message = AsyncMock()
    state = AsyncMock()
    back_to = AsyncMock()

    message.text = "+81234567890"  # Неправильный формат номера
    await process_phone_number(message, state, back_to)

    message.answer.assert_called_once_with(
        "Неверный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX."
    )
    back_to.assert_not_called()
