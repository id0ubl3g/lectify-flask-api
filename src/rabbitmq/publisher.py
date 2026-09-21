
from src.rabbitmq.connection import get_connection
import pika
import json

QUEUE_ARGUMENTS = {'x-max-priority': 3}

def publish_message(queue: str, message: dict, priority: int = 1) -> None:

    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(
        queue=queue,
        durable=True,
        arguments=QUEUE_ARGUMENTS
    )

    channel.basic_publish(
        exchange='',
        routing_key=queue,
        body=json.dumps(message),
        properties=pika.BasicProperties(priority=priority)
    )

    connection.close()