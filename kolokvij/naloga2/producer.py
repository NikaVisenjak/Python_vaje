import pika       # knjiznica za komunikacijo z RabbitMQ
import random     # za generiranje nakljucnih stevil
import time       # za sleep med posiljanjem

RABBITMQ_HOST = 'localhost'  # naslov RabbitMQ streznika

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))  # vzpostavimo TCP povezavo z RabbitMQ
    channel = connection.channel()  # odpremo kanal znotraj povezave (vecina operacij gre skozi kanal)

    # (1) Queue za naloge - ime generira RabbitMQ (exclusive, auto-delete)
    result = channel.queue_declare(queue='', exclusive=True)  # queue='' pomeni: RabbitMQ sam izbere edinstveno ime; exclusive=True: queue se izbrise ko se povezava zapre
    task_queue = result.method.queue  # preberemo ime, ki ga je dodelil RabbitMQ
    print(f"Task queue: {task_queue}")  # izpisemo ime task queue-ja

    # (2) Queue za rezultate - ime generira RabbitMQ
    result2 = channel.queue_declare(queue='', exclusive=True)  # enako kot zgoraj, a za rezultate
    result_queue = result2.method.queue  # preberemo ime result queue-ja
    print(f"Result queue: {result_queue}")  # izpisemo ime result queue-ja

    with open('queue_names.txt', 'w') as f:  # odpremo datoteko za pisanje
        f.write(f"{task_queue}\n{result_queue}\n")  # zapisemo imeni queue-jev, vsako v svojo vrstico
    print("Imeni quejev shranjeni v queue_names.txt\n")  # potrdimo zapis

    pairs = []  # seznam poslanih parov (da vemo koliko rezultatov pricakujemo)
    for i in range(10):  # ponovimo 10x - posljemo 10 nalog
        a = random.randint(1, 5)  # nakljucno stevilo med 1 in 5
        b = random.randint(1, 5)  # drugo nakljucno stevilo med 1 in 5
        msg = f"{a},{b}"          # sestavimo sporocilo v obliki "a,b" npr. "3,5"
        pairs.append(msg)         # dodamo par v seznam (za stevec rezultatov)

        channel.basic_publish(
            exchange='',            # prazen exchange = direktno v queue (default exchange)
            routing_key=task_queue, # ime queue-ja kamor posljemo sporocilo
            body=msg.encode(),      # vsebina sporocila kot bytes
            properties=pika.BasicProperties(delivery_mode=2)  # delivery_mode=2: sporocilo je persistentno (prezivi restart RabbitMQ)
        )
        print(f"[{i+1}/10] Poslano: {msg}")  # izpisemo katero sporocilo smo poslali
        time.sleep(1)  # pocakamo 1 sekundo pred naslednjim posiljanjem

    print(f"\nVseh 10 nalog poslanih. Čakam na {len(pairs)} rezultatov...\n")  # obvestimo da smo poslali vse

    received = 0  # stevec prejetih rezultatov
    for method, properties, body in channel.consume(result_queue, auto_ack=True):  # blokirajoce cakamo na sporocila iz result_queue; auto_ack=True: sporocilo potrdimo takoj
        print(f"Rezultat: {body.decode()}")  # izpisemo rezultat npr. "3x5=15"
        received += 1  # povecamo stevec
        if received >= len(pairs):  # ce smo prejeli vse rezultate
            break  # prekinemo zanko

    channel.cancel()      # prekinemo consume (sprostimo kanal)
    connection.close()    # zapremo povezavo z RabbitMQ
    print("\nVse naloge dokončane!")  # koncno sporocilo

if __name__ == '__main__':
    main()  # zazenemo main funkcijo
