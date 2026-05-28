
from src.rabbitmq.connection import get_connection
import json

def publish_message(queue: str, message: dict) -> None:

    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(
        queue=queue,
        durable=True
    )

    channel.basic_publish(
        exchange='',
        routing_key=queue,
        body=json.dumps(message)
    )

    connection.close()