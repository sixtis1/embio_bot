import re
import logging
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
import html
from database.questions_db import (
    save_question_to_db,
    get_patient_name_by_tg_id,
)
from configuration.config_db import get_client
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
support_group_id = os.getenv("SUPPORT_GROUP_ID")


def markdown_escape(text: str) -> str:
    # Экранируем текст для HTML
    return html.escape(text)


async def send_question_to_support(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    question_text = message.text
    patient_name = get_patient_name_by_tg_id(user_id)

    if not patient_name:
        first_name = "Без имени"
        last_name = ""
    else:
        first_name = patient_name["first_name"]
        last_name = patient_name["last_name"]

    response = save_question_to_db(user_id, first_name, last_name, question_text)

    if response and response.data:
        question_id = response.data[0]["id"]
        status = "открыт✅"

        support_message = (
            f"❓Вопрос №{question_id}.\n\n"
            f"Пациент: {markdown_escape(first_name)} {markdown_escape(last_name)}\n"
            f"Вопрос: {markdown_escape(question_text)}\n\n"
            f"Статус вопроса: {status}\n\n"
            f"Ответьте на это сообщение, чтобы отправить ответ пациенту."
        )

        support_msg = await message.bot.send_message(
            support_group_id, support_message, parse_mode="HTML"
        )

        await state.update_data(
            support_msg_id=support_msg.message_id, question_id=question_id
        )

        await message.answer(
            "Ваш вопрос был отправлен в службу поддержки. Мы свяжемся с вами как можно скорее."
        )
    else:
        await message.answer(
            "Произошла ошибка при отправке вашего вопроса. Пожалуйста, попробуйте снова."
        )


def extract_question_id_from_message(text: str) -> int:
    # Ищем ID после "Вопрос №" и перед первым символом ':'
    match = re.search(r"Вопрос №(\d+).", text)
    if match:
        return int(match.group(1))
    else:
        logger.error("Не удалось извлечь ID вопроса из текста сообщения.")


def get_patient_tg_id_from_question_id(question_id: int) -> int:
    supabase_client = get_client()
    try:
        response = (
            supabase_client.table("patient_questions")
            .select("patient_tg_id")
            .eq("id", question_id)
            .execute()
        )
        if response.data:
            return response.data[0]["patient_tg_id"]
        else:
            logger.error("Пациент с данным ID вопроса не найден.")
    except Exception as e:
        logger.exception(f"Error retrieving patient TG ID: {e}")
        raise
