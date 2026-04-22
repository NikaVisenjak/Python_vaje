import pika

credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

exchange_name = 'myDirectExchange'
channel.exchange_declare(exchange=exchange_name, exchange_type='direct')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# binding za vse
for key in ['info', 'warning', 'error']:
    channel.queue_bind(exchange=exchange_name, 
                       queue=queue_name, 
                       routing_key=key)
    
def callback(ch, method, properties, body):
    print(f"[ALL] {method.routing_key}: {body.decode()}")

channel.basic_consume(queue=queue_name, 
                      on_message_callback=callback, 
                      auto_ack=True)

print('App 1 - printing all messages...')
channel.start_consuming()