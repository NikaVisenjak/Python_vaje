import pika

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('localhost', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

MY_QUEUE = 'NiKi'

channel.queue_declare(queue=MY_QUEUE)
 
def callback(ch, method, properties, body):
    print(f"Prejeto sporocilo: {body.decode()}")
 
channel.basic_consume(queue=MY_QUEUE, on_message_callback=callback, auto_ack=True)
 
print(f"Poslusan na queue '{MY_QUEUE}'. Cakam na sporocila...")
channel.start_consuming()