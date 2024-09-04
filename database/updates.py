from datetime import datetime

from database.constants_db import logger


async def replace_content(
    start_time, message, first_name_clients, first_name_doctor, last_name_doctor
):
    try:
        # Попробуем несколько форматов времени
        formats = ["%Y-%m-%dT%H:%M:%S%z", "%d.%m.%Y %H:%M"]
        start_time_datetime = None
        for fmt in formats:
            try:
                start_time_datetime = datetime.strptime(start_time, fmt)
                break
            except ValueError:
                logger.exception("Ошибка при изменении времени")
                continue

        if not start_time_datetime:
            logger.exception(
                "Переданное время не соответствовало ни одному из форматов"
            )
            return message

        day = start_time_datetime.strftime("%d.%m")
        month_and_time = start_time_datetime.strftime("%H:%M")
        formatted_start_time = f"{day} в {month_and_time}"

        # Подготавливаем словарь с заменами
        placeholders = {
            "{first_name}": first_name_clients,
            "{first_name_doctor}": first_name_doctor,
            "{last_name_doctor}": last_name_doctor,
            "{start_time}": formatted_start_time,
        }

        # Замена содержимого в сообщении
        content = message.get("content", "")
        for placeholder, value in placeholders.items():
            if placeholder in content:
                content = content.replace(placeholder, value)
        message["content"] = content

        # Замена шаблонов во времени сообщения, если необходимо
        if "time" in message:
            time_content = message.get("time", "")
            for placeholder, value in placeholders.items():
                if placeholder in time_content:
                    time_content = time_content.replace(placeholder, value)
            message["time"] = time_content

        return message
    except Exception as e:
        logger.error(f"Ошибка при замене флагов в сообщении: {e}")
        return message
