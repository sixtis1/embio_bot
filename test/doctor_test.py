from unittest.mock import AsyncMock, patch

import pytest
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import keyboards.doctor_kb as kb
from handlers.doctor import (
    handler_doctor_command,
    my_patients_handler,
    find_patient_by_surname_handler,
    find_patient_command,
    treatment_stage_callback,
    back_to_menu,
)
from states.states_doctor import DoctorStates


@pytest.mark.asyncio
async def test_my_patients_handler():
    # проверяет обработчик кнопки 'Мои пациенты' в меню

    message = AsyncMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # настраиваем мок для метода message.answer
    message.answer = AsyncMock()

    # проверяем, что бот отправляет сообщение о этапах лечения и обновляет состояние
    await my_patients_handler(message, state)

    message.answer.assert_called()
    state.set_state.assert_called_once_with(DoctorStates.my_patients)


@pytest.mark.asyncio
async def test_find_patient_by_surname_handler():
    # проверяет обработчик кнопки 'Найти пациента по фамилии'

    message = AsyncMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # настраиваем мок для метода message.answer
    message.answer = AsyncMock()
    # проверяем, что бот просит ввести фамилию пациента и обновляет состояние
    await find_patient_by_surname_handler(message, state)

    message.answer.assert_called_once_with(
        "Введите фамилию по образцу: Иванова", reply_markup=kb.doctor_reply_only_back()
    )
    state.set_state.assert_called_once_with(DoctorStates.find_patient_by_surname)


@pytest.mark.asyncio
async def test_back_to_menu():
    # проверяет обработчик кнопки 'Назад'

    message = AsyncMock(spec=types.Message)
    state = AsyncMock(spec=FSMContext)

    # настраиваем мок для метода message.answer
    message.answer = AsyncMock()

    # задаем текущее состояние
    state.set_state = AsyncMock()

    # проверяем, что бот отправляет сообщение и обновляет состояние
    await back_to_menu(message, state)

    message.answer.assert_called_once_with(
        "Выберите действие в меню", reply_markup=kb.doctor_menu_keyboard()
    )
    state.set_state.assert_called_once_with(DoctorStates.menu)
