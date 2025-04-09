import motor.motor_asyncio
import datetime
import os

ip = os.getenv("MONGO_IP")

class MongoReportStorage:
    def __init__(self, connection_string=f'mongodb://{ip}/', database_name='security'):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
            self.db = self.client[database_name]
            self.reports_collection = self.db['reports']
            self.alerts_collection = self.db['alerts']
            self.block_collection = self.db['block']
            print("MongoDB connection established successfully.")
        except Exception as e:
            print(f"Error establishing MongoDB connection: {e}")
    
    async def store_report(self, 
                            user_id: int, 
                            server_id: int, 
                            reported_user_id: int, 
                            reason: str, 
                            imagen_files: list = None):
        
        timestamp = int(datetime.datetime.now().timestamp())
        
        report_doc = {
            'reported_user_id': reported_user_id,
            'reason': reason,
            'timestamp': timestamp,
            'imagen_urls': []
        }
        
        try:
            if imagen_files:
                if isinstance(imagen_files, list):
                    report_doc['imagen_urls'] = imagen_files
                else:
                    for file in imagen_files:
                        if hasattr(file, 'url'):
                            report_doc['imagen_urls'].append(file.url)
            
            result = await self.reports_collection.insert_one(report_doc)
            print(f"Report stored successfully. Document ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            print(f"Error storing report in database: {e}")
            return None
    
    async def get_user_reports(self, user_id: int):
        try:
            cursor = self.reports_collection.find({'reported_user_id': user_id})
            reports = await cursor.to_list(length=None)
            return reports
        except Exception as e:
            print(f"Error retrieving reports: {e}")
            return []
    
    async def get_all_reports(self):
        try:
            cursor = self.reports_collection.find({})
            reports = await cursor.to_list(length=None)
            return reports
        except Exception as e:
            print(f"Error retrieving all reports: {e}")
            return []
    
    async def update_report_reason(self, user_id: int, new_reason: str, report_id=None):
        try:
            if report_id:
                filter_query = {'_id': report_id}
            else:
                filter_query = {'reported_user_id': user_id}
            
            result = await self.reports_collection.update_many(
                filter_query,
                {'$set': {'reason': new_reason}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating report reason: {e}")
            return False
    
    async def delete_report(self, report_id):
        try:
            result = await self.reports_collection.delete_one({'_id': report_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting report: {e}")
            return False
    
    async def delete_user_reports(self, user_id: int):
        try:
            result = await self.reports_collection.delete_many({'reported_user_id': user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting user reports: {e}")
            return False
    
    async def add_image_to_report(self, user_id: int, image_url: str, report_id=None):
        try:
            if report_id:
                report = await self.reports_collection.find_one({'_id': report_id})
            else:
                report = await self.reports_collection.find_one({'reported_user_id': user_id})
            
            if not report:
                return False
            
            current_urls = report.get('imagen_urls', [])
            
            if len(current_urls) >= 8:
                return False
            
            update_result = await self.reports_collection.update_one(
                {'_id': report['_id']},
                {'$push': {'imagen_urls': image_url}}
            )
            
            return update_result.modified_count > 0
        except Exception as e:
            print(f"Error adding image to report: {e}")
            return False
    
    async def remove_image_from_report(self, user_id: int, image_index: int, report_id=None):
        try:
            if report_id:
                report = await self.reports_collection.find_one({'_id': report_id})
            else:
                report = await self.reports_collection.find_one({'reported_user_id': user_id})
            
            if not report:
                return False
            
            imagen_urls = report.get('imagen_urls', [])
            
            if image_index >= len(imagen_urls) or image_index < 0:
                return False
            
            imagen_urls.pop(image_index)
            
            update_result = await self.reports_collection.update_one(
                {'_id': report['_id']},
                {'$set': {'imagen_urls': imagen_urls}}
            )
            
            return update_result.modified_count > 0
        except Exception as e:
            print(f"Error removing image from report: {e}")
            return False
    
    async def get_server_alerts(self, server_id: int):
        try:
            server_data = await self.alerts_collection.find_one({'_id': str(server_id)})
            if server_data:
                return server_data
            else:
                return {
                    '_id': str(server_id),
                    'channel': 0,
                    'perms': [0],
                    'message': '',
                    'language': 'es' 
                }
        except Exception as e:
            print(f"Error retrieving server alerts: {e}")
            return {
                '_id': str(server_id),
                'channel': 0,
                'perms': [0],
                'message': '',
                'language': 'es'
            }
    
    async def update_server_alerts(self, server_id: int, field: str, value):
        try:
            await self.alerts_collection.update_one(
                {'_id': str(server_id)},
                {'$set': {field: value}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating server alerts: {e}")
            return False
    
    async def update_server_alerts_full(self, server_id: int, data: dict):
        try:
            data['_id'] = str(server_id)
            await self.alerts_collection.replace_one(
                {'_id': str(server_id)},
                data,
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating full server alerts: {e}")
            return False
    
    async def get_blocked_servers(self):
        try:
            block_doc = await self.block_collection.find_one({'_id': 'servers'})
            if block_doc:
                return block_doc.get('servers', [])
            else:
                await self.block_collection.insert_one({'_id': 'servers', 'servers': []})
                return []
        except Exception as e:
            print(f"Error retrieving blocked servers: {e}")
            return []
    
    async def add_blocked_server(self, server_id):
        try:
            block_doc = await self.block_collection.find_one({'_id': 'servers'})
            if block_doc:
                if server_id not in block_doc.get('servers', []):
                    await self.block_collection.update_one(
                        {'_id': 'servers'},
                        {'$push': {'servers': server_id}}
                    )
                    return True
                return False
            else:
                await self.block_collection.insert_one({'_id': 'servers', 'servers': [server_id]})
                return True
        except Exception as e:
            print(f"Error adding blocked server: {e}")
            return False
    
    async def remove_blocked_server(self, server_id):
        try:
            block_doc = await self.block_collection.find_one({'_id': 'servers'})
            if block_doc and server_id in block_doc.get('servers', []):
                await self.block_collection.update_one(
                    {'_id': 'servers'},
                    {'$pull': {'servers': server_id}}
                )
                return True
            return False
        except Exception as e:
            print(f"Error removing blocked server: {e}")
            return False

mongo_report_storage = MongoReportStorage()