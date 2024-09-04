import asyncio
import logging

from aiogram import Bot

from handlers.admin import admin_router
from handlers.doctor import doctor_router
from handlers.patient import patient_router
from handlers.auth import auth_router
from scheduler.scheduler_init import scheduler
from scheduler.sched_tasks import update_database_scheduler, set_cleaning_database
from scheduler.appointment_scheduler import check_new_appointments
from configuration.config_bot import bot, dp


async def on_startup():
    scheduler.add_job(update_database_scheduler, trigger="interval", minutes=30)
    scheduler.add_job(check_new_appointments, trigger="interval", minutes=30)
    scheduler.add_job(set_cleaning_database, trigger="interval", days=90)

async def main():
    scheduler.ctx.add_instance(bot, declared_class=Bot)
    scheduler.start()

    auth_router.include_router(doctor_router)
    auth_router.include_router(patient_router)
    auth_router.include_router(admin_router)
    dp.include_router(auth_router)

    await bot.delete_webhook(drop_pending_updates=True)
    admin_router.bot = bot

    await on_startup()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
