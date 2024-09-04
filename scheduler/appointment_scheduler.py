import logging
from datetime import datetime, timedelta
from configuration.config_db import get_client
from scheduler.scenario_helpers import (
    get_telegram_id,
    get_procedure_scenarios,
    determine_content_type,
)
from scheduler.scheduler_init import scheduler
from scheduler.sched_tasks import (
    schedule_scenario_message,
    schedule_check_for_procedure_4331,
)

supabase = get_client()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Функция для вычисления времени отправки
async def calculate_send_time(start_time, offset_time):
    start_datetime = datetime.fromisoformat(start_time)
    try:
        if " " in offset_time:
            days_offset, time_of_day = offset_time.split()
            time_offset = int(days_offset)
            send_time = start_datetime + timedelta(hours=time_offset)
            return datetime.combine(
                send_time.date(), datetime.strptime(time_of_day, "%H:%M").time()
            )
        elif offset_time == "0":
            return datetime.now() + timedelta(seconds=5)
        else:
            time_offset = int(offset_time)
            send_time = start_datetime + timedelta(hours=time_offset)
            return send_time
    except ValueError:
        logging.error(f"Invalid time format: {offset_time}")
        return None


async def get_new_appointments():
    response = (
        supabase.table("appointments").select("*").eq("processed", False).execute()
    )
    if response.data:
        logging.info(f"New appointments found: {len(response.data)}")
        return response.data
    else:
        logging.info("No new appointments found")
    return []


async def mark_appointment_as_processed(appointment_id):
    supabase.table("appointments").update({"processed": True}).eq(
        "id", appointment_id
    ).execute()


# Обработчик новой записи
async def handle_new_appointment(appointment):
    procedure_id = appointment["procedure_id"]
    telegram_id = await get_telegram_id(appointment["client_id"])
    if not telegram_id:
        return

    if procedure_id == 4331:
        # Если процедура имеет ID 4331, планируем проверку через 8 дней
        await schedule_check_for_procedure_4331(
            scheduler,
            appointment["client_id"],
            await calculate_send_time(appointment["start_time"], "0"),
        )
        await mark_appointment_as_processed(appointment["id"])
        return

    scenarios = await get_procedure_scenarios(telegram_id)
    if scenarios and "messages" in scenarios:
        for message in scenarios["messages"]:
            send_time = await calculate_send_time(
                appointment["start_time"], message["time"]
            )
            if send_time:
                message_type = await determine_content_type(message)
                id_survey = message.get("id_survey")
                await schedule_scenario_message(
                    scheduler,
                    telegram_id,
                    message["id"],
                    send_time,
                    message["content"],
                    message["url"],
                    message_type,
                    id_survey=id_survey if id_survey else -1,
                )
            else:
                logging.warning(
                    f"Skipping message {message['id']} due to invalid time format"
                )
        await mark_appointment_as_processed(appointment["id"])
    else:
        await mark_appointment_as_processed(appointment["id"])
        logging.info(f"No messages found for procedure {procedure_id}")


# Функция для проверки новых записей и их обработки
async def check_new_appointments():
    logging.info("Checking for new appointments...")
    new_appointments = await get_new_appointments()
    for appointment in new_appointments:
        await handle_new_appointment(appointment)
