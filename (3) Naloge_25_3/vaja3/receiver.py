import pika

credentials = pika.PlainCredentials('guest', 'guest')
parameters =  pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

exchange_name = "AnimalTopicExchange"

channel.exchange_declare(exchange=exchange_name, 
                         exchange_type='topic')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue


channel.queue_bind(queue=queue_name, 
                   exchange=exchange_name,
                   routing_key="*.fox.*")

def callback(ch, method, properties, body):
    message = body.decode()
    routing_key = method.routing_key

    print(f"Received: {routing_key} -> {message}")

    size, animal, typ = routing_key.split(".")

    # resend samo za big fox
    if size == "big" and animal == "fox" and typ != "resend":
        new_key = "big.fox.resend"

        channel.basic_publish(exchange=exchange_name, 
                              routing_key=new_key,
                              body=message)
        
channel.basic_consume(queue=queue_name, 
                      on_message_callback=callback, 
                      auto_ack=True)

print("waiting for messages...")
channel.start_consuming()
