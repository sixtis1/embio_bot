from configuration.config_db import get_client
from database.constants_db import logger


supabase = get_client()


def get_survey_by_id(survey_id):
    try:
        # Получаем запись из таблицы surveys по id опроса
        survey_response = (
            supabase.table("surveys").select("file").eq("id", survey_id).execute()
        )

        if not survey_response.data:
            return {"result": {"code": 1, "err_msg": "Опрос не найден"}}

        survey_file = survey_response.data[0]["file"]

        return {"result": {"file": survey_file, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении опроса: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}


def add_to_result_in_survey(tg_id, value):
    try:
        # Обновляем значение в столбце survey_result таблицы clients для пациента с указанным tg_id
        update_response = (
            supabase.table("clients")
            .update({"survey_result": value})
            .eq("tg_id", tg_id)
            .execute()
        )

        if not (
            update_response.data
            and isinstance(update_response.data, list)
            and len(update_response.data) > 0
        ):
            return {"result": {"code": 1, "err_msg": "Ошибка при обновлении данных"}}

        return {"result": {"code": 0, "message": "Данные успешно обновлены"}}

    except Exception as e:
        logger.exception(f"Ошибка при получении опроса: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}


def add_survey_answers(tg_id, answers):
    try:
        # Получаем текущие результаты опросов из базы данных
        response = (
            supabase.table("clients")
            .select("surveys_answers")
            .eq("tg_id", tg_id)
            .execute()
        )

        # Проверка успешности запроса
        if not response.data:
            return {
                "result": {
                    "code": 1,
                    "err_msg": "Пользователь с данным tg_id не найден",
                }
            }

        # Извлекаем существующие результаты опросов
        existing_results = response.data[0].get("surveys_answers")

        # Если поле пустое (null), инициализируем его пустым списком
        if existing_results is None:
            existing_results = []

        # Добавляем новые результаты опроса к существующим
        existing_results.append(answers)

        # Обновляем поле surveys_results в базе данных
        update_response = (
            supabase.table("clients")
            .update({"surveys_answers": existing_results})
            .eq("tg_id", tg_id)
            .execute()
        )

        # Проверка успешности обновления
        if not update_response.data:
            return {"result": {"code": 1, "err_msg": "Ошибка при обновлении данных"}}

        return {"result": {"code": 0, "message": "Данные успешно обновлены"}}

    except Exception as e:
        logger.exception(f"Ошибка при добавлении ответов на опрос: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}


def get_doctor_by_client_tg_id(client_tg_id):
    try:
        # Получаем ID клиента по его tg_id
        client_response = (
            supabase.table("clients").select("id").eq("tg_id", client_tg_id).execute()
        )

        if not client_response.data:
            return {"result": {"code": 1, "err_msg": "Доктор не найден"}}

        client_id = client_response.data[0]["id"]

        # Получаем список пациентов для заданного доктора
        appointments_response = (
            supabase.table("appointments")
            .select("doctor:doctors(tg_id)")
            .eq("client_id", client_id)
            .execute()
        )

        if not appointments_response.data:
            return {"result": {"code": 1, "err_msg": "Пациенты не найдены"}}

        # Формируем список пациентов
        doctors = [
            {
                "tg_id": appointment["doctor"]["tg_id"],
            }
            for appointment in appointments_response.data
        ]

        return {"result": {"doctors": doctors, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении врача по tg_id пациента: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}


def get_client_name_by_tg_id(client_tg_id):
    try:
        # Получаем имя и фамилию клиента по его tg_id
        client_response = (
            supabase.table("clients")
            .select("first_name", "last_name", "phone_number", "stage")
            .eq("tg_id", client_tg_id)
            .execute()
        )

        if not client_response.data:
            return {"result": {"code": 1, "err_msg": "Клиент не найден"}}

        # Извлекаем имя и фамилию клиента
        client_data = client_response.data[0]
        first_name = client_data.get("first_name", "Имя не указано")
        last_name = client_data.get("last_name", "Фамилия не указана")
        phone_number = client_data.get("phone_number", "Телефон не указан")
        stage = client_data.get("stage", "Сценарий не указан")

        return {
            "result": {
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "stage": stage,
                "code": 0,
            }
        }

    except Exception as e:
        logger.exception(f"Ошибка при получении имени пациента по tg_id: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}
