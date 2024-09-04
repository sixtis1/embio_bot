import datetime
import pytz

from configuration.config_db import get_client
from database.constants_db import procedure_to_stage_number, logger
from database.updates import replace_content

from datetime import datetime, timedelta

supabase = get_client()
global current_procedure
current_procedure = ""


async def all_crm_ids():
    all_id = []
    client_response = supabase.table("clients").select("id_crm").execute()
    for client in client_response.data:
        all_id.append(client["id_crm"])
    return all_id


def process_appointment(appointment, crm_id):
    procedure_id = appointment["id_tov"]
    doctor_full_name = appointment["s_name"]
    start_time_str = appointment["dt_beg"]
    end_time_str = appointment["dt_end"]
    room_name = appointment["z_name"]

    # Преобразуем строки времени в объекты datetime
    start_time = datetime.strptime(start_time_str, "%d.%m.%Y %H:%M")
    end_time = datetime.strptime(end_time_str, "%d.%m.%Y %H:%M")

    # Преобразуем время в формат ISO 8601
    start_time_iso = start_time.astimezone(pytz.UTC).isoformat()
    end_time_iso = end_time.astimezone(pytz.UTC).isoformat()

    # Извлекаем имя и фамилию врача
    name_parts = doctor_full_name.split()
    if len(name_parts) < 2:
        return None  # Пропускаем, если имя врача некорректное
    first_name, last_name = name_parts[1], name_parts[0]

    # Получаем ID врача
    doctor_response = (
        supabase.table("doctors")
        .select("id, id_crm")
        .eq("first_name", first_name)
        .eq("last_name", last_name)
        .execute()
    )
    doctor_data = doctor_response.data
    if not doctor_data:
        return None  # Пропускаем, если врач не найден
    doctor_id = doctor_data[0].get("id")

    # Получаем ID клиента и текущий этап
    client_response = (
        supabase.table("clients")
        .select("id, stage")
        .eq("id_crm", crm_id)
        .single()
        .execute()
    )
    client_data = client_response.data
    if not client_data:
        return None  # Пропускаем, если клиент не найден
    client_id = client_data.get("id")
    current_stage = client_data.get("stage")

    # Возвращаем всю необходимую информацию
    return {
        "procedure_id": procedure_id,
        "doctor_id": doctor_id,
        "doctor_crm_id": doctor_data[0].get("id_crm"),
        "client_id": client_id,
        "current_stage": current_stage,
        "start_time_iso": start_time_iso,
        "end_time_iso": end_time_iso,
        "room_name": room_name,
        "doctor_first_name": first_name,
        "doctor_last_name": last_name,
    }


async def update_clients_sheduler(crm_id, response):
    global current_procedure
    if not (response and "result" in response and "items" in response["result"]):
        return

    appointments = response["result"]["items"]
    scheduler_stage = {}
    current_time = datetime.utcnow().isoformat()

    for appointment in appointments:
        appointment_info = process_appointment(appointment, crm_id)
        if not appointment_info:
            continue  # Пропускаем, если данные некорректные или отсутствуют

        # Определяем данные для вставки или обновления
        appointment_data = {
            "procedure_id": appointment_info["procedure_id"],
            "doctor_id": appointment_info["doctor_id"],
            "client_id": appointment_info["client_id"],
            "start_time": appointment_info["start_time_iso"],
            "end_time": appointment_info["end_time_iso"],
            "room_name": appointment_info["room_name"],
            "processed": False,
        }
        current_stage = appointment_info["current_stage"]
        first_name = appointment_info["doctor_first_name"]
        last_name = appointment_info["doctor_last_name"]
        # Добавляем запись в словарь
        stage_number = procedure_to_stage_number.get(
            appointment_info["procedure_id"], 0
        )
        if stage_number != 0:
            if stage_number in scheduler_stage:
                stage_number += 0.1
            scheduler_stage[stage_number] = appointment_data
        else:
            stage_number = max(scheduler_stage.keys(), default=1) + 0.1
            scheduler_stage[stage_number] = appointment_data

    for stage_number, current_scheduler in sorted(scheduler_stage.items()):
        client_id = current_scheduler["client_id"]
        is_procedure = current_scheduler["procedure_id"]

        existing_appointment_response = (
            supabase.table("appointments")
            .select("id, procedure_id, processed, end_time")
            .eq("client_id", client_id)
            .execute()
        )
        existing_appointment_data = existing_appointment_response.data

        if existing_appointment_data:
            first_appointment = existing_appointment_data[0]
            is_processed = first_appointment["processed"]
            existing_end_time = first_appointment["end_time"]

            if is_processed:
                if (
                    not (is_procedure in procedure_to_stage_number)
                    and current_time >= existing_end_time
                ):
                    current_scheduler["processed"] = True
                    supabase.table("appointments").update(current_scheduler).eq(
                        "id", first_appointment["id"]
                    ).execute()
                else:
                    # Если процедура соответствует текущему этапу
                    if procedure_to_stage_number.get(
                        is_procedure
                    ) == procedure_to_stage_number.get(current_procedure):
                        current_scheduler["processed"] = True
                        supabase.table("appointments").update(current_scheduler).eq(
                            "id", first_appointment["id"]
                        ).execute()
                    # Если процедура должна следовать за текущей по этапу или по времени
                    elif procedure_to_stage_number.get(
                        is_procedure
                    ) > procedure_to_stage_number.get(current_procedure):
                        current_stage = procedure_to_stage_number[is_procedure]
                        current_procedure = current_scheduler["procedure_id"]
                        supabase.table("clients").update({"stage": current_stage}).eq(
                            "id", client_id
                        ).execute()
                        await update_users_scenarios(
                            current_scheduler["procedure_id"],
                            client_id,
                            current_scheduler["start_time"],
                            first_name,
                            last_name,
                            current_stage,
                            appointment_info["doctor_crm_id"],
                        )
                        supabase.table("appointments").update(current_scheduler).eq(
                            "id", first_appointment["id"]
                        ).execute()

        else:
            # Если записи нет, создаем новую
            current_procedure = current_scheduler["procedure_id"]
            supabase.table("appointments").insert(current_scheduler).execute()
            await update_users_scenarios(
                current_scheduler["procedure_id"],
                client_id,
                current_scheduler["start_time"],
                first_name,
                last_name,
                current_stage,
                current_scheduler["doctor_id"],
            )


async def update_users_scenarios(
    procedure_id,
    client_id,
    start_time,
    first_name_doctor,
    last_name_doctor,
    stage,
    id_doctor,
):
    if procedure_id in procedure_to_stage_number and isinstance(stage, int):
        # Получаем сценарии для текущего этапа
        scenarios_response = (
            supabase.table("scenarios")
            .select("scenarios_msg")
            .eq("stage", stage)
            .execute()
        )
        scenarios_data = scenarios_response.data

        # Получаем информацию о клиенте (tg_id, имя)
        client_response = (
            supabase.table("clients")
            .select("first_name", "tg_id")
            .eq("id", client_id)
            .execute()
        )
        client_data = client_response.data
        if not client_data:
            logger.exception("Пациент с таким id не был найден")
            return

        client_info = client_data[0]  # Предполагаем, что у клиента только одна запись
        tg_id = client_info.get("tg_id")
        first_name_clients = client_info.get("first_name")

        if scenarios_data:
            # Получаем данные о сценариях и сообщениях
            scenarios = scenarios_data[0]["scenarios_msg"]

            # Ищем процедуру, соответствующую переданному procedure_id
            procedure = next(
                (p for p in scenarios["procedures"] if p["id"] == procedure_id), None
            )
            if not procedure:
                logger.exception(
                    f"Процедура с ID {procedure_id} не найдена в сценариях"
                )
                return

            for message in scenarios["messages"]:
                message_id = message.get("id")

                if message_id in procedure["message_ids"]:
                    # Замена контента в сообщении
                    updated_message = await replace_content(
                        start_time,
                        message,
                        first_name_clients,
                        first_name_doctor,
                        last_name_doctor,
                    )

                    # Формируем format_id для поиска URL
                    format_id = f"{stage}.{message_id}.{id_doctor}"

                    # Получаем URL видео для данного сообщения
                    video_url = await get_url(format_id)

                    if video_url:
                        updated_message["url"] = video_url

                    # Обновляем сценарий с измененным сообщением
                    for idx, msg in enumerate(scenarios["messages"]):
                        if msg["id"] == message_id:
                            scenarios["messages"][idx] = updated_message
                            break

            # Проверка существования записи для данного клиента на конкретном этапе
            existing_record_response = (
                supabase.table("users_scenarios")
                .select("*")
                .eq("clients_id", tg_id)
                .execute()
            )

            existing_record_data = existing_record_response.data

            if existing_record_data:
                # Если запись существует, обновляем её
                supabase.table("users_scenarios").update(
                    {
                        "stage_msg": stage,
                        "scenarios": scenarios,
                    }
                ).eq("id", existing_record_data[0].get("id")).execute()
            else:
                # Если записи нет, создаем новую
                supabase.table("users_scenarios").insert(
                    {
                        "stage_msg": stage,
                        "scenarios": scenarios,
                        "clients_id": tg_id,
                    }
                ).execute()


async def get_url(format_id_url):
    response = (
        supabase.table("video")
        .select("video_link")
        .eq("for_scenarios", format_id_url)
        .execute()
    )
    video_data = response.data
    if video_data:
        return video_data[0].get("video_link")
    else:
        logger.warning(f"Для сценария {format_id_url} не найдено видео.")
        return None


async def clearing_supabase():
    months_ago = datetime.now() - timedelta(days=30)

    response = (
        supabase.table("appointments")
        .select("*")
        .eq("procedure_id", 4331)
        .lt("start_time", months_ago.isoformat())
        .execute()
    )

    if response.data:
        clients_to_delete = [record["client_id"] for record in response.data]

        tg_ids_to_delete = []
        for client_id in clients_to_delete:
            client_response = (
                supabase.table("clients").select("tg_id").eq("id", client_id).execute()
            )
            if client_response.data:
                tg_ids_to_delete.append(client_response.data[0]["tg_id"])

        for client_id in clients_to_delete:
            supabase.table("appointments").delete().eq("client_id", client_id).execute()

        for tg_id in tg_ids_to_delete:
            supabase.table("users_scenarios").delete().eq("clients_id", tg_id).execute()

        for client_id in clients_to_delete:
            supabase.table("clients").delete().eq("id", client_id).execute()

    else:
        logger.exception("Записей для удаление не было найдено")
