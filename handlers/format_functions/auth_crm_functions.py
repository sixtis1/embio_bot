import re
from datetime import datetime, timedelta
from configuration.config_crm import get_information


async def get_user_data(phone):
    data = {"command": "get_user_data", "user": phone}
    return await get_information(data)


async def get_sotr_data(phone):
    data = {"command": "get_sotr", "phone": phone}
    return await get_information(data)


async def get_book_data(client_id):
    today = datetime.today()
    beg_per = (today - timedelta(days=7)).strftime("%d.%m.%Y")
    end_per = (today + timedelta(days=2)).strftime("%d.%m.%Y")

    data = {
        "command": "get_book",
        "id": client_id,
        "beg_per": beg_per,
        "end_per": end_per,
    }

    return await get_information(data)


async def find_first_stage_trigger(client_id):
    response = await get_book_data(client_id)

    # Извлекаем список items
    items = response["result"]["items"]

    # Словарь триггеров с числовыми значениями для первого этапа
    first_stage_triggers = [1559, 1566]

    first_stage_trigger = None

    for item in items:
        if not isinstance(item, dict):
            continue

        id_tov = item.get("id_tov")
        if id_tov is None:
            continue

        if id_tov in first_stage_triggers:
            first_stage_trigger = (
                list(first_stage_triggers).index(id_tov) + 1
            )  # Сохраняем номер этапа

            break  # Выходим из цикла, как только нашли первый этап

    return first_stage_trigger


async def authenticate_patient(phone, additional_info, state):
    response = await get_user_data(phone)
    if response.get("result", {}).get("code") == 0:
        user_info = response["result"]
        passport_digits = re.findall(r"\d+", user_info.get("passport", ""))
        if passport_digits:
            passport_last_digits = passport_digits[-1][-4:]
            if passport_last_digits == additional_info:
                # Найти последний триггер этапа по идентификатору клиента
                client_id = user_info["id"]
                stage_number = await find_first_stage_trigger(client_id)

                await state.update_data(
                    name=user_info["name"],
                    passport=passport_last_digits,
                    id_crm=client_id,
                    stage=stage_number,  # Обновляем числовое значение стадии
                )

                return True
    return False


async def authenticate_doctor(phone, additional_info, state):
    response = await get_sotr_data(phone)
    if response.get("result", {}).get("code") == 0:
        sotr_info = response["result"]["item"]
        if str(sotr_info["id"]) == additional_info:
            await state.update_data(
                name=sotr_info["full_name"],
                specialty=sotr_info["dolj"],
                id_crm=sotr_info["id"],
            )
            return True
    return False
