from dotenv import load_dotenv
import pika
import os

load_dotenv()

def get_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(
        username=os.getenv('RABBITMQ_USER'),
        password=os.getenv('RABBITMQ_PASS')
    )

    parameters = pika.ConnectionParameters(
        host='localhost',
        credentials=credentials
    )

    return pika.BlockingConnection(parameters)