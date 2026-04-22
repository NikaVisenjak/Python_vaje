import pika
import threading
import sys
import uuid

EXCHANGE_NAME = 'chatroom'
MY_ID = str(uuid.uuid4())  # Unikatni ID za to sejo

def make_callback(my_id):
    def callback(ch, method, properties, body):
        msg = body.decode()
        sender_id, _, text = msg.partition('|')
        if sender_id == my_id:
            return  # Ignoriraj svoja sporočila
        sys.stdout.write('\r' + ' ' * 40 + '\r')
        print(text)
        sys.stdout.write('> ')
        sys.stdout.flush()
    return callback

def receive(channel, my_id):
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=make_callback(my_id), auto_ack=True)
    channel.start_consuming()

def send(channel, username, my_id):
    while True:
        sys.stdout.write('> ')
        sys.stdout.flush()
        msg = input()
        if msg.strip() == '':
            continue
        # Format: "uuid|[IME]: sporocilo"
        full_msg = f"{my_id}|[{username}]: {msg}"
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=full_msg)

if __name__ == '__main__':
    username = input("Vnesite svoje ime: ").strip()

    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters('127.0.0.1', credentials=credentials)

    recv_connection = pika.BlockingConnection(parameters)
    recv_channel = recv_connection.channel()
    recv_channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    send_connection = pika.BlockingConnection(parameters)
    send_channel = send_connection.channel()
    send_channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout')

    recv_thread = threading.Thread(target=receive, args=(recv_channel, MY_ID), daemon=True)
    recv_thread.start()

    print(f"Dobrodošli v chatroom, {username}! (Ctrl+C za izhod)\n")

    try:
        send(send_channel, username, MY_ID)
    except KeyboardInterrupt:
        print("\nOdhajate iz chatrooma.")
    finally:
        send_connection.close()
        recv_connection.close()