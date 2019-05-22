import json
from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer
from .tasks import getDayAheadPrices
from project.celery import app
from asgiref.sync import async_to_sync


class FetchPricesConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        getDayAheadPrices.delay(self.channel_name)

    def receive(self, message):
        pass
    
    def disconnect(self, close_code):
        self.close()

    def send_results(self, event):
        self.send_json(content=event['text'])
