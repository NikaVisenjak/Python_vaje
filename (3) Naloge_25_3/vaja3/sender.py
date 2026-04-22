import pika

credentials = pika.PlainCredentials('guest', 'guest')
parameters =  pika.ConnectionParameters('127.0.0.1', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

exchange_name = "AnimalTopicExchange"

channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

# tuple
messages = [
    ("big.fox.original", "Big fox message 1"),
    ("small.fox.original", "Small fox message 2"),
    ("big.cat.original", "Big cat message 3"),
    ("big.fox.original", "Big fox message 4"),
]

for key, message in messages:
    channel.basic_publish(exchange=exchange_name,
                          routing_key=key,
                          body=message)
    print(f"Sent: {key} -> {message}")

connection.close()