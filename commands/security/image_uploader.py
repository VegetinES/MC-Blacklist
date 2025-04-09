import aiohttp
import base64
from typing import Optional
import os

key = os.getenv("IMG_KEY")

async def upload_image_to_imgbb(image_bytes: bytes) -> Optional[str]:
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://api.imgbb.com/1/upload",
                data={
                    "key": key,
                    "image": base64_image
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['url']
                else:
                    print(f"Error al subir imagen: {response.status}")
                    return None
        except Exception as e:
            print(f"Error en upload_image_to_imgbb: {e}")
            return None