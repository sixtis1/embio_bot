from configuration.config_db import get_client

supabase = get_client()


async def get_procedure_scenarios(client_id):
    response = (
        supabase.table("users_scenarios")
        .select("scenarios")
        .eq("clients_id", client_id)
        .execute()
    )
    if response.data:
        scenario_data = response.data[0]
        scenarios = scenario_data["scenarios"]
        return scenarios
    return None


async def get_telegram_id(client_id):
    response = supabase.table("clients").select("tg_id").eq("id", client_id).execute()
    if response.data:
        return response.data[0]["tg_id"]
    return None


async def determine_content_type(message):
    if "video" in message["type"]:
        return "text video"
    elif "image" in message["type"]:
        return "text image"
    elif "survey" in message["type"]:
        return "survey"
    else:
        return "text"
