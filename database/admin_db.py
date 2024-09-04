from configuration.config_db import get_client
from database.constants_db import logger

from dotenv import load_dotenv


load_dotenv()


supabase = get_client()


async def get_info_patient_number_surname(info, by_what):
    try:
        # Определяем, по какому полю делать запрос
        field = "phone_number" if by_what == "phone_number" else "last_name"

        # Запрашиваем данные клиентов из таблицы
        client_response = (
            supabase.table("clients")
            .select("id, first_name, last_name, phone_number, stage")
            .eq(field, info)
            .execute()
        )

        client_data_list = client_response.data

        # Если данные не найдены, возвращаем None
        if not client_data_list:
            return None

        results = []

        for client_data in client_data_list:
            client_id = client_data["id"]

            doctor_response = (
                supabase.table("appointments")
                .select("doctor:doctors(first_name, last_name)")
                .eq("client_id", client_id)
                .limit(1)
                .execute()
            )

            if not doctor_response.data:
                doctor_data = {"first_name": "", "last_name": ""}
            else:
                doctor_item = doctor_response.data[0]
                doctor_data = doctor_item["doctor"]

            # Формируем результат для текущего клиента
            result = {
                "patient_id": client_id,
                "patient_name": f"{client_data.get('first_name', '')} {client_data.get('last_name', '')}",
                "patient_phone": client_data.get("phone_number", ""),
                "stage": client_data.get("stage", ""),
                "doctor_name": f"{doctor_data.get('first_name', '')} {doctor_data.get('last_name', '')}",
            }

            results.append(result)

        return {"result": {"items": results, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при поиске пациента:{e}")
        return None


async def find_all_doctors():
    try:
        doctor_response = (
            supabase.table("doctors").select("id, first_name, last_name").execute()
        )

        if doctor_response.data:

            result = [
                {
                    "doctor_id": doctor["id"],
                    "doctor_name": f"{doctor['first_name']} {doctor['last_name']}",
                }
                for doctor in doctor_response.data
            ]
            return {"result": {"items": result, "code": 0}}
        else:
            return None
    except Exception as e:
        logger.exception(f"Ошибка при получении списка врачей:{e}")
        return None


async def find_all_patients(doctor_id):
    try:
        patient_response = (
            supabase.table("appointments")
            .select("client:clients(first_name, last_name, phone_number, id, stage)")
            .eq("doctor_id", doctor_id)
            .execute()
        )

        if patient_response.data:

            result = [
                {
                    "patient_id": patient["client"]["id"],
                    "patient_name": f"{patient['client']['first_name']} {patient['client']['last_name']}",
                    "patient_phone": patient["client"]["phone_number"],
                    "stage": patient["client"]["stage"],
                }
                for patient in patient_response.data
            ]
            return {"result": {"items": result, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении списка пациентов:{e}")
        return None


async def find_patient_scenarios(phone_number):
    try:
        # Поиск информации о клиенте по номеру телефона
        client_response = (
            supabase.table("clients")
            .select("id, tg_id")
            .eq("phone_number", phone_number)
            .execute()
        )
        client_data = client_response.data
        if not client_data:
            return {"error": "Клиент не найден"}

        client_id = client_data[0]["id"]
        client_tg = client_data[0]["tg_id"]

        scenarios_response = (
            supabase.table("users_scenarios")
            .select("id, scenarios")
            .eq("clients_id", client_tg)
            .execute()
        )
        scenarios_data = scenarios_response.data
        if not scenarios_data:
            return {"error": "Сценарии не найдены"}

        # Формирование результата
        result = [
            {
                "scenario_id": scenario["id"],
                "messages": scenario["scenarios"].get("messages", []),
                "name_stage": scenario["scenarios"].get("name_stage", ""),
                "procedures": scenario["scenarios"].get("procedures", []),
            }
            for scenario in scenarios_data
        ]

        return {"result": {"items": result, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении сценария пациента:{e}")
        return {"error": str(e)}


async def update_supabase(endpoint: str, data: dict, record_id: int):
    try:
        response = supabase.table(endpoint).update(data).eq("id", record_id).execute()

        # Проверка, содержит ли ответ обновленные данные
        if response.data and isinstance(response.data, list) and len(response.data) > 0:
            return {"status": "success", "message": "Update successful"}
        else:
            error_message = (
                response.error_message
                if hasattr(response, "error_message")
                else "Unknown error"
            )
            return {"status": "error", "message": error_message}

    except Exception as e:
        logger.exception(f"Ошибка при обновлении записи в Supabase: {e}")
        return {"status": "error", "message": str(e)}


async def get_all_scenarios():
    try:
        response = supabase.table("scenarios").select("id, scenarios_msg").execute()

        if not response.data:
            return None

        # Сортировка этапов по их ID
        result = sorted(
            [
                {
                    "scenario_id": scenario["id"],
                    "name_stage": scenario["scenarios_msg"].get(
                        "name_stage", "Без названия"
                    ),
                }
                for scenario in response.data
            ],
            key=lambda x: x["scenario_id"],  # Сортировка по ID этапа
        )

        return {"result": {"items": result, "code": 0}}

    except Exception as e:
        logger.exception(f"Ошибка при получении сценариев: {e}")
        return None


async def get_scenario_data(scenario_id):
    try:
        response = (
            supabase.table("scenarios")
            .select("scenarios_msg")
            .eq("id", scenario_id)
            .single()
            .execute()
        )

        if not response.data:
            return None

        scenario_data = response.data["scenarios_msg"]
        return scenario_data

    except Exception as e:
        logger.exception(f"Ошибка при получении данных сценария: {e}")
        return None


async def save_edited_message(scenario_id, unique_messages):
    scenario_data = await get_scenario_data(scenario_id)
    if not scenario_data:
        raise Exception("Failed to retrieve scenario data")

    scenario_data["messages"] = unique_messages

    await update_supabase("scenarios", {"scenarios_msg": scenario_data}, scenario_id)


async def save_edited_time(scenario_id, message_id, new_time, unique_messages):
    for message in unique_messages:
        if message["id"] == message_id:
            message["time"] = new_time
            break

    await save_edited_message(scenario_id, unique_messages)


async def find_id_doctor(tg_id):
    try:
        # Запрашиваем данные клиентов из таблицы
        client_response = (
            supabase.table("clients").select("id").eq("tg_id", tg_id).execute()
        )
        client_id = client_response.data[0]["id"]

        doctor_response = (
            supabase.table("appointments")
            .select("doctors(id_crm)")
            .eq("client_id", client_id)
            .execute()
        )
        doctor_data = doctor_response.data
        doctor_id = doctor_data[0]["doctors"]["id_crm"]

        result = {"doctor_id": doctor_id}
        return result

    except Exception as e:
        logger.exception(f"Ошибка при поиске врача:{e}")
        return None
