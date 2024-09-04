from configuration.config_db import get_client
from database.constants_db import logger

supabase = get_client()


def get_patients_by_doctor_phone(phone):
    try:
        # Получаем ID доктора по его телефону
        doctor_response = (
            supabase.table("doctors").select("id").eq("phone_number", phone).execute()
        )

        if not doctor_response.data:
            return {"result": {"code": 1, "err_msg": "Доктор не найден"}}

        doctor_id = doctor_response.data[0]["id"]

        # Получаем список пациентов для заданного доктора
        appointments_response = (
            supabase.table("appointments")
            .select(
                "client:clients(first_name, last_name, tg_id, phone_number, stage, survey_result)"
            )
            .eq("doctor_id", doctor_id)
            .execute()
        )

        if not appointments_response.data:
            return {"result": {"code": 1, "err_msg": "Пациенты не найдены"}}

        # Формируем список пациентов
        patients = [
            {
                "first_name": appointment["client"]["first_name"],
                "last_name": appointment["client"]["last_name"],
                "tg_id": appointment["client"]["tg_id"],
                "phone_number": appointment["client"]["phone_number"],
                "stage": appointment["client"]["stage"],
                "survey_result": appointment["client"]["survey_result"],
            }
            for appointment in appointments_response.data
        ]

        return {"result": {"patients": patients, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении пациентов по номеру врача: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}


def get_patient_surveys_answers_by_phone(phone):
    try:
        # Получаем запись из таблицы clients по phone_number
        client_response = (
            supabase.table("clients")
            .select("surveys_answers")
            .eq("phone_number", phone)
            .execute()
        )

        if not client_response.data:
            return None

        surveys_file = client_response.data[0]

        return surveys_file

    except Exception as e:
        logger.exception(f"Ошибка при получении ответов на опросы: {e}")
        return None
