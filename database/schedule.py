from configuration.config_db import get_client
from database.constants_db import logger

supabase = get_client()


def get_schedule_by_tg_id(tg_id):
    try:
        # Получаем ID клиента по tg_id
        client_response = (
            supabase.table("clients").select("id").eq("tg_id", tg_id).execute()
        )

        if not client_response.data:
            return {"result": {"code": 1, "err_msg": "Клиент не найден"}}

        client_id = client_response.data[0]["id"]

        # Получаем расписание клиента по client_id
        schedule_response = (
            supabase.table("appointments")
            .select(
                "procedure:procedures(name), doctor:doctors(first_name, last_name), start_time"
            )
            .eq("client_id", client_id)
            .execute()
        )

        if not schedule_response.data:
            return {"result": {"code": 1, "err_msg": "Записи не найдены"}}

        # Формируем нужный ответ с только необходимыми полями
        schedule_item = schedule_response.data[0]
        result = {
            "start_time": schedule_item["start_time"],
            "procedure_name": schedule_item["procedure"]["name"],
            "doctor_first_name": schedule_item["doctor"]["first_name"],
            "doctor_last_name": schedule_item["doctor"]["last_name"],
        }

        return {"result": {"item": result, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении расписания: {e}")
        return {"result": {"code": 1, "err_msg": str(e)}}
