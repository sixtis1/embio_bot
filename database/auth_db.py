from crm.informations_update import set_sheduler
from database.constants_db import logger
from configuration.config_db import get_client


async def get_scenarios_for_stage(stage):
    client = get_client()
    url = "scenarios"
    try:
        response = (
            client.table(url).select("scenarios_msg").eq("stage", stage).execute()
        )
        if response.data:
            return response.data[0]["scenarios_msg"]
        else:
            logger.error(f"Сценарии для стадии {stage} не найдены")
            return None
    except Exception as e:
        logger.exception(f"Ошибка при получении сценария: {e}")
        return None


async def get_client_info(tg_id):
    client = get_client()
    clients_url = "clients"
    try:
        response = client.table(clients_url).select("*").eq("tg_id", tg_id).execute()
        if response.data:
            return response.data[0]
        else:
            logger.error(f"Клиент с tg_id {tg_id} не найден")
            return None
    except Exception as e:
        logger.exception(f"Ошибка при получении информации о пациенте: {e}")
        return None


async def save_client_data(
    tg_id, first_name, last_name, passport, phone_number, id_crm, stage=None
):
    client = get_client()
    clients_url = "clients"

    try:
        # Проверяем наличие клиента в базе
        existing_client_response = (
            client.table(clients_url).select("id").eq("tg_id", tg_id).execute()
        )

        if not existing_client_response.data:
            # Если клиента нет, добавляем его
            data = {
                "tg_id": tg_id,
                "first_name": first_name,
                "last_name": last_name,
                "passport": passport,
                "phone_number": phone_number,
                "id_crm": id_crm,
                "stage": stage,
            }
            client.table(clients_url).upsert(data).execute()

        # Передаем данные дальше
        await set_sheduler(id_crm)

    except Exception as e:
        logger.exception(f"Ошибка попытке сохранить пациента Supabase: {e}")


async def save_doctor_data(
    first_name, last_name, specialty, phone_number, id_crm, tg_id
):
    client = get_client()
    url = "doctors"  # таблица врачей
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "specialty": specialty,
        "phone_number": phone_number,
        "id_crm": id_crm,
        "tg_id": tg_id,
    }
    try:
        response = client.table(url).insert(data).execute()
        if response.data:
            return response.data
        else:
            logger.error(f"Ошибка в сохранении врача: {response.error}")
            return None
    except Exception as e:
        logger.exception(f"Ошибка попытке сохранить врача в Supabase:{e}")
        return None


async def check_if_admin(tg_id):
    client = get_client()
    admins_url = "admins"
    try:
        response = (
            client.table(admins_url).select("*").eq("admin_tg_id", tg_id).execute()
        )
        if response.data:
            return True
        return False
    except Exception as e:
        logger.exception(f"Ошибка при проверке администратора:{e}")
        return False
