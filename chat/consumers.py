# TRIGGERING ONMESSAGE EVENT
# chat/consumers.py
import asyncio
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from chat.views import build_summary
from chat.lang import get_categories


class SummaryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        if text_data_json['message'] == 'get_summary':
            username = text_data_json['username']
            categories = await get_categories()
            
            # Run the long-running method in a separate thread
            loop = asyncio.get_event_loop()
            for category in categories:
                summary = await loop.run_in_executor(None, self.get_summary, username, category)
                if summary != None:
                    await self.send(text_data=json.dumps({'summary': summary}))
                    
            await self.send(text_data=json.dumps({'summary': 'END'}))

    def get_summary(self, username, category):
        html = build_summary(username, category)
        return html
