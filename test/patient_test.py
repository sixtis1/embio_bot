from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

import keyboards.constants as kc
import keyboards.patient_kb as kb
from handlers.patient import (
    handle_patient_command,
    question_handler,
    answer_question_handler,
)
from states.states_patient import PatientStates


@pytest.mark.asyncio
async def test_handle_patient_command():
    # тест проверяет, что команда /patient отправляет меню и устанавливает состояние patientstates.menu
    message = AsyncMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # настраиваем мок для метода message.answer
    message.answer = AsyncMock()

    # запускаем тестируемую функцию
    await handle_patient_command(message, state)

    # проверяем, что метод message.answer был вызван с правильными аргументами
    message.answer.assert_called_once_with(
        "Выберите действие в меню: ", reply_markup=kb.patient_menu_keyboard()
    )
    # проверяем, что состояние было установлено в patientstates.menu
    state.set_state.assert_called_once_with(PatientStates.menu)


@pytest.mark.asyncio
async def test_answer_question_handler_back():
    # тест проверяет обработчик ответа на вопрос при выборе кнопки "назад"
    message = AsyncMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # Тестируем сценарий, где сообщение содержит кнопку "назад"
    message.text = kc.buttons_patient_question["back"]
    message.content_type = "text"  # Устанавливаем правильный тип контента

    # настраиваем мок для метода message.answer
    message.answer = AsyncMock()

    # запускаем тестируемую функцию
    await answer_question_handler(message, state)

    # проверяем, что метод message.answer был вызван с правильными аргументами
    message.answer.assert_called_once_with(
        "Выберите действие", reply_markup=kb.patient_menu_keyboard()
    )

    # проверяем, что состояние было установлено в PatientStates.menu
    state.set_state.assert_called_once_with(PatientStates.menu)


@pytest.mark.asyncio
async def test_question_handler():
    # Создаем моки для message и state
    message = MagicMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # Создаем мок для from_user и настраиваем его атрибут id
    from_user = MagicMock()
    from_user.id = 12345

    # Настраиваем message.from_user на созданный мок
    message.from_user = from_user

    message.answer = AsyncMock()

    # Мокаем функцию has_unanswered_question, чтобы она возвращала True
    with patch("handlers.patient.has_unanswered_question", return_value=True):
        # Запускаем тестируемую функцию
        await question_handler(message, state)

        # Проверяем, что message.answer был вызван с правильным аргументом
        message.answer.assert_called_once_with(
            "Ваш вопрос уже был отправлен в поддержку. Пожалуйста, дождитесь ответа."
        )
        # Проверяем, что состояние не было изменено
        state.set_state.assert_not_called()

    # Мокаем функцию has_unanswered_question, чтобы она возвращала False
    with patch("handlers.patient.has_unanswered_question", return_value=False):
        # Сбросим счетчики вызовов
        message.answer.reset_mock()
        state.set_state.reset_mock()

        await question_handler(message, state)

        # Проверяем, что message.answer был вызван с правильным аргументом
        message.answer.assert_called_once_with(
            "Задайте свой вопрос, который отправится в поддержку: ",
            reply_markup=kb.patient_question_keyboard(),
        )
        # Проверяем, что состояние было изменено на ask_question
        state.set_state.assert_called_once_with(PatientStates.ask_question)


@pytest.mark.asyncio
async def test_answer_question_handler_text():
    # Создаем моки для message и state
    message = MagicMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # Настроим моки для message
    message.content_type = "text"
    message.text = "Текст вопроса"

    # Мокаем функцию send_question_to_support
    with patch(
        "handlers.patient.send_question_to_support", new=AsyncMock()
    ) as mock_send_question_to_support:
        # Настраиваем message.answer как AsyncMock
        message.answer = AsyncMock()

        # Запускаем тестируемую функцию
        await answer_question_handler(message, state)

        # Проверяем, что send_question_to_support был вызван
        mock_send_question_to_support.assert_called_once_with(message, state)

        # Проверяем, что message.answer был вызван с правильным аргументом
        message.answer.assert_called_once_with(
            "Вопрос отправлен. Что вы хотите сделать дальше?",
            reply_markup=kb.patient_question_cancel_keyboard(),
        )
        # Проверяем, что состояние было изменено на PatientStates.awaiting_response
        state.set_state.assert_called_once_with(PatientStates.awaiting_response)


@pytest.mark.asyncio
async def test_answer_question_handler_non_text():
    # Создаем моки для message и state
    message = MagicMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # Настроим моки для message
    message.content_type = "photo"  # Неверный формат
    message.text = "Неправильный текст"

    # Настраиваем message.answer как AsyncMock
    message.answer = AsyncMock()

    # Запускаем тестируемую функцию
    await answer_question_handler(message, state)

    # Проверяем, что message.answer был вызван с правильным аргументом
    message.answer.assert_called_once_with(
        "Неверный формат вопроса. Пожалуйста, введите только текст вопроса.",
        reply_markup=kb.patient_question_keyboard(),
    )
    # Проверяем, что состояние не было изменено
    state.set_state.assert_not_called()
