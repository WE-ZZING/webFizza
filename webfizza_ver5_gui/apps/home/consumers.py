from channels.generic.websocket import AsyncWebsocketConsumer
import json
import os
import signal

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "log_group"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print("Disconnected:", close_code)

    async def receive(self, text_data):
        if text_data == "ping":  # Ping 메시지를 받으면 Pong 응답
            await self.send("pong")
        else:
            log_data = json.loads(text_data)
            message = log_data.get("message", "No message")
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "log_message", "message": message}
            )

    async def log_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))
        print(f"Sent log message to client: {message}")

class InputConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "input_group"
        print("WebSocket connection established at /ws/input/")
        await self.accept()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with close code: {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')

        print(f"Received message: {message}")

        if message == "ctrl+c":
            print("[InputConsumer] Shutdown signal (ctrl+c) sent.")
            await self.send(text_data=json.dumps({"message": "ctrl+c"}))
        else:
            print(f"[InputConsumer] Unknown message: {message}")
