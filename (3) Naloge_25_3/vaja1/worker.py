import pika
import time

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

MY_QUEUE = 'myQueue123'

channel.queue_declare(queue=MY_QUEUE, durable=True, arguments={'x-queue-type': 'quorum'})

def callback(ch, method, properties, body):
    print(f"Received {int(body)}")
    time.sleep(int(body))
    print(f"Task {int(body)} completed!")
     #Ročno ack, ker ni nujno, da task opravimo!
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue=MY_QUEUE, 
                      auto_ack=False, 
                      on_message_callback=callback)

print(f"Waiting for messages...")
channel.start_consuming()


