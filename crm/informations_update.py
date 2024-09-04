import datetime

from configuration.config_crm import get_information
from database.supabase_helpers import update_clients_sheduler, all_crm_ids


async def get_tovs():
    data = {"command": "get_tovs"}
    return await get_information(data)


async def set_sheduler(all_ids=None):
    if all_ids == None:
        all_ids = await all_crm_ids()
    elif isinstance(all_ids, int):
        all_ids = [all_ids]

    for crm_id in all_ids:
        if crm_id != None:
            data = {
                "command": "get_book",
                "id": crm_id,
                "beg_per": datetime.datetime.now().strftime("%d.%m.%Y"),
                "end_per": (
                    datetime.datetime.now() + datetime.timedelta(days=7)
                ).strftime("%d.%m.%Y"),
            }

            # Выполняем запрос к CRM для каждого `id_crm`
            response = await get_information(data)
            await update_clients_sheduler(crm_id, response)
        else:
            continue
