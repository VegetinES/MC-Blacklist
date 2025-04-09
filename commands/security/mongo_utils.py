from .mongo import mongo_report_storage

async def get_server_data(server_id):
    return await mongo_report_storage.get_server_alerts(server_id)

async def get_specific_field(server_id, field=None):
    server_data = await get_server_data(server_id)
    if not server_data:
        return None
    
    if field == 'security':
        return server_data
    
    if field and field in server_data:
        return server_data.get(field)
    
    return server_data

async def update_server_data(server_id, field, value):
    return await mongo_report_storage.update_server_alerts(server_id, field, value)

async def update_full_server_data(server_id, data):
    return await mongo_report_storage.update_server_alerts_full(server_id, data)

async def get_server_language(server_id):
    data = await get_server_data(server_id)
    if data and "language" in data:
        return data.get("language")
    return "es"