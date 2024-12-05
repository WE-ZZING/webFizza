import json
from channels.generic.websocket import AsyncWebsocketConsumer

class InputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        task = text_data_json['task']
        url = text_data_json.get('url', '')
        file = text_data_json.get('file', '')

        # WebFizza.py로 전달할 메시지 생성
        message = {
            'task': task,
            'url': url,
            'file': file,
        }

        # 메시지를 WebSocket 서버로 전송
        await self.channel_layer.group_send(
            'webfizza_group',
            {
                'type': 'webfizza.message',
                'message': message
            }
        )

    async def webfizza_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
