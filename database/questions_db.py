from datetime import datetime
from configuration.config_db import get_client
import logging

logger = logging.getLogger(__name__)


def get_patient_name_by_tg_id(tg_id):
    # Получает имя и фамилию пациента из таблицы clients по tg_id

    supabase_client = get_client()

    try:
        # Выполняем запрос для получения данных из таблицы clients
        response = (
            supabase_client.table("clients")
            .select("first_name, last_name")
            .eq("tg_id", tg_id)
            .execute()
        )

        if response.data:
            # Возвращаем словарь с именем и фамилией
            return response.data[0]
        else:
            return None
    except Exception as e:
        logger.exception(
            f"Ошибка при получении имени пациента из таблицы клиентов: {e}"
        )
        return None


def save_question_to_db(patient_tg_id, first_name, last_name, question_text):
    supabase_client = get_client()

    # Преобразуем datetime в строку в формате ISO
    now = datetime.utcnow().isoformat()

    data = {
        "patient_tg_id": patient_tg_id,
        "first_name": first_name,
        "last_name": last_name,
        "question_text": question_text,
        "status": False,  # False означает, что вопрос не ответен
        "created_at": now,
        "updated_at": now,
    }

    try:
        response = supabase_client.table("patient_questions").insert(data).execute()
        return response
    except Exception as e:
        logger.exception(f"Ошибка при сохранении вопроса в базу данных: {e}")
        return None


def has_unanswered_question(tg_id):
    supabase_client = get_client()

    try:
        # Выполняем запрос для получения данных из таблицы patient_questions
        response = (
            supabase_client.table("patient_questions")
            .select("id")
            .eq("patient_tg_id", tg_id)
            .eq("status", False)  # Ищем только те вопросы, которые еще не были отвечены
            .execute()
        )

        if response.data:
            # Если есть хотя бы одна запись, возвращаем True
            return True
        else:
            return False
    except Exception as e:
        logger.exception(f"Ошибка при проверке наличия неотвеченных вопросов: {e}")
        return False


def is_question_answered(question_id: int) -> bool:
    supabase_client = get_client()

    try:
        # Выполняем запрос для получения статуса вопроса
        response = (
            supabase_client.table("patient_questions")
            .select("status")
            .eq("id", question_id)
            .execute()
        )

        if response.data:
            return response.data[0]["status"]
        else:
            logger.error("Вопрос с данным ID не найден.")
    except Exception as e:
        logger.exception(f"Ошибка при проверке статуса вопроса: {e}")
        raise


def update_question_response(question_id, support_response):
    supabase_client = get_client()

    data = {
        "status": True,  # Вопрос ответен
        "support_response": support_response,
        "updated_at": datetime.utcnow().isoformat(),  # Преобразуем datetime в строку
    }

    try:
        response = (
            supabase_client.table("patient_questions")
            .update(data)
            .eq("id", question_id)
            .execute()
        )
        return response
    except Exception as e:
        logger.exception(f"Ошибка при сохранении ответа на вопрос в базу данных: {e}")
        return None


def cancel_question_in_db(question_id: int):
    supabase_client = get_client()

    data = {
        "status": True,  # Обновляем статус на True, что означает, что вопрос закрыт
        "updated_at": datetime.utcnow().isoformat(),  # Преобразуем datetime в строку
    }

    try:
        response = (
            supabase_client.table("patient_questions")
            .update(data)
            .eq("id", question_id)
            .execute()
        )
        return response
    except Exception as e:
        logger.exception(f"Ошибка при отмене вопроса в базе данных: {e}")
        return None
