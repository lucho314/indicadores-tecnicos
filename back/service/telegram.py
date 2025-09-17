import os
import requests
from config import TELEGRAM_BOT_TOKEN
class TelegramService:
    def __init__(self):
        token = TELEGRAM_BOT_TOKEN
        if not token:
            raise ValueError("⚠️ La variable de entorno TELEGRAM_BOT_TOKEN no está definida")
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, chat_id: int, text: str):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        response = requests.post(url, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error enviando mensaje: {response.text}")
        return response.json()
