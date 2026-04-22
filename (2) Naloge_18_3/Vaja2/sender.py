import pika
import time

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

MY_QUEUE = 'NiKi'

channel.queue_declare(queue=MY_QUEUE)
 
i = 1
for _ in iter(int, 1):  # neskoncna zanka
    channel.basic_publish(exchange='', routing_key=MY_QUEUE, body=str(i))
    print(f"Poslano sporocilo: {i}")
    i += 1
    time.sleep(1)