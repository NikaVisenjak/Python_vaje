import pika
import random

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

MY_QUEUE = 'myQueue123'

channel.queue_declare(queue=MY_QUEUE, durable=True, arguments={'x-queue-type': 'quorum'})

properties = pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)

for i in range(10):
    RandNumber = random.randint(5,15)
    data = str(RandNumber)
    channel.basic_publish(exchange='',
                      routing_key=MY_QUEUE,
                      body=data,
                      properties=properties)
    print(f"Poslan {data}.")

connection.close()
