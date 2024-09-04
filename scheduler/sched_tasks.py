import logging
from datetime import datetime, timedelta
import asyncio

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import URLInputFile

from scheduler.scheduler_init import scheduler as sched
from configuration.config_db import get_client
from configuration.config_bot import dp
from crm.informations_update import set_sheduler
from database.supabase_helpers import clearing_supabase
from handlers.patient import switch_survey
from scheduler.scenario_helpers import (
    get_procedure_scenarios,
    get_telegram_id,
    determine_content_type,
)

supabase = get_client()
send_lock = asyncio.Lock()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def update_database_scheduler():
    await set_sheduler()


async def set_cleaning_database():
    await clearing_supabase()


def split_message_to_two_parts(message, max_length):
    if len(message) <= max_length:
        return [message]

    middle_index = len(message) // 2
    split_index = message.rfind(".", 0, middle_index)
    if split_index == -1:
        split_index = message.rfind(" ", 0, middle_index)
        if split_index == -1:
            split_index = middle_index

    part1 = message[: split_index + 1].strip()
    part2 = message[split_index + 1 :].strip()

    return [part1, part2]


async def send_scenario_message(
    bot: Bot, telegram_id, message_id, content, url, message_type, id_survey
):
    async with send_lock:
        parts = split_message_to_two_parts(
            content, 4096 if message_type == "text" else 1024
        )

        state_with: FSMContext = FSMContext(
            storage=dp.storage,
            key=StorageKey(chat_id=telegram_id, user_id=telegram_id, bot_id=bot.id),
        )

        match message_type:
            case "text":
                for part in parts:
                    await bot.send_message(chat_id=telegram_id, text=part)

            case "text video":
                video = URLInputFile(url)
                await bot.send_video(chat_id=telegram_id, video=video, caption=parts[0])

            case "text image":
                photo = URLInputFile(url)
                await bot.send_photo(chat_id=telegram_id, photo=photo, caption=parts[0])

            case "video/audio":
                media = URLInputFile(url)
                await bot.send_video(chat_id=telegram_id, video=media, caption=parts[0])

            case "survey":
                await switch_survey(state_with, telegram_id, id_survey)

            case _:
                logging.error(f"Unknown message type: {message_type}")

        if len(parts) > 1:
            await bot.send_message(chat_id=telegram_id, text=parts[1])


async def schedule_scenario_message(
    scheduler, telegram_id, message_id, send_time, content, url, message_type, id_survey
):
    parts = split_message_to_two_parts(
        content, 4096 if message_type == "text" else 1024
    )
    first_part = parts.pop(0)
    job_kwargs = {
        "telegram_id": telegram_id,
        "message_id": message_id,
        "content": first_part,
        "url": url,
        "message_type": message_type,
        "id_survey": id_survey,
    }
    scheduler.add_job(
        send_scenario_message,
        "date",
        run_date=send_time + timedelta(seconds=(message_id + 1) * 2),
        kwargs=job_kwargs,
        replace_existing=True,
    )

    if parts:
        send_time = send_time + timedelta(seconds=5)
        for part in parts:
            scheduler.add_job(
                send_scenario_message,
                "date",
                run_date=send_time,
                kwargs={
                    "telegram_id": telegram_id,
                    "message_id": message_id,
                    "content": part,
                    "url": "",
                    "message_type": "text",
                    "id_survey": id_survey,
                },
                replace_existing=True,
            )


async def schedule_check_for_procedure_4331(scheduler, client_id, appointment_time):
    # Вычисляем время проверки через 8 дней
    check_time = appointment_time + timedelta(days=8)
    logging.info(f"schedule_check_for_procedure_4331 at {check_time}")
    # Добавляем задачу в планировщик
    scheduler.add_job(
        check_and_send_4331_scenario,
        "date",
        run_date=check_time,
        kwargs={"client_id": client_id},
        replace_existing=True,
    )


async def check_and_send_4331_scenario(client_id):
    response = (
        supabase.table("appointments").select("*").eq("client_id", client_id).execute()
    )
    appointments = response.data if response.data else []

    procedure_to_check = [4332, 4333, 4334]
    found = any(
        appointment["procedure_id"] in procedure_to_check
        for appointment in appointments
    )

    if not found:
        scenario_id = 4331
        scenarios = await get_procedure_scenarios(scenario_id)
        telegram_id = await get_telegram_id(client_id)

        if scenarios and "messages" in scenarios:
            for message in scenarios["messages"]:
                send_time = datetime.now() + timedelta(seconds=10)
                message_type = await determine_content_type(message)
                await schedule_scenario_message(
                    sched,
                    telegram_id,
                    message["id"],
                    send_time,
                    message["content"],
                    message["url"],
                    message_type,
                )
        else:
            logging.warning(f"No messages found for scenario {scenario_id}")
