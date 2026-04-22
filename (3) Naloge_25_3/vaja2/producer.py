import pika
import random
import time
import datetime

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

exchange_name = 'myDirectExchange'
channel.exchange_declare(exchange=exchange_name, exchange_type='direct')

keys = ['info', 'warning', 'error']

while True:
    time.sleep(2)
    key = random.choice(keys)
    channel.basic_publish(exchange = exchange_name,
                          routing_key = key,
                          body = str(datetime.datetime.now()))
    print(f"Message {key} sent.")