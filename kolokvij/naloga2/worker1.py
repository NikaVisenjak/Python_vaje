import pika  # knjiznica za komunikacijo z RabbitMQ
import time  # za sleep pri cakanju na queue_names.txt

RABBITMQ_HOST = 'localhost'  # naslov RabbitMQ streznika

def get_queue_names():
    for _ in range(30):  # poskusamo do 30x (30 sekund), da pocakamo na producerja
        try:
            with open('queue_names.txt', 'r') as f:  # preberemo datoteko z imeni queue-jev
                lines = f.read().strip().split('\n')  # razdelimo po vrsticah
                if len(lines) == 2:                   # ce sta obe imeni zapisani
                    return lines[0], lines[1]          # vrnemo (task_queue, result_queue)
        except FileNotFoundError:
            pass  # datoteka se ne obstaja, pocakamo
        print("Čakam na queue_names.txt ...")  # obvestimo da cakamo
        time.sleep(1)  # pocakamo sekundo in poskusimo znova
    raise RuntimeError("queue_names.txt ni bil najden!")  # ce po 30s se vedno ni datoteke, vrzemo napako

def main():
    task_queue, result_queue = get_queue_names()  # preberemo imeni queue-jev iz datoteke
    print(f"Worker 1 (normalen) - task queue: {task_queue}, result queue: {result_queue}\n")  # izpisemo katera queue-ja bomo uporabljali

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))  # vzpostavimo TCP povezavo z RabbitMQ
    channel = connection.channel()  # odpremo kanal za komunikacijo

    channel.basic_qos(prefetch_count=1)  # fair dispatch: worker dobi novo nalogo sele ko zakljuci prejsnjo (ne dobi vseh naenkrat)

    def callback(ch, method, properties, body):  # funkcija se poklic ko prejmemo sporocilo; ch=kanal, method=metapodatki, body=vsebina
        msg = body.decode()              # pretvorimo bytes v string npr. "3,5"
        a, b = map(int, msg.split(','))  # razdelimo po vejici in pretvorimo v stevilki
        rezultat = a * b                 # izracunamo zmnozek
        odgovor = f"{a}x{b}={rezultat}" # sestavimo odgovor npr. "3x5=15"
        print(f"[Worker 1] Obdelano: {msg} -> {odgovor}")  # izpisemo kaj smo obdelali

        ch.basic_publish(
            exchange='',             # prazen exchange = direktno v queue
            routing_key=result_queue,# posljemo v result queue (ne task queue)
            body=odgovor.encode(),   # vsebina kot bytes
            properties=pika.BasicProperties(delivery_mode=2)  # persistentno sporocilo
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)  # potrdimo RabbitMQ da smo nalogo uspesno obdelali (sicer bi jo RabbitMQ poslal znova)

    channel.basic_consume(queue=task_queue, on_message_callback=callback)  # registriramo callback funkcijo za task_queue
    print("Worker 1 čaka na naloge...")  # obvestimo da smo pripravljeni
    channel.start_consuming()  # zazenemo blokirajoce cakanje na sporocila (neskoncna zanka)

if __name__ == '__main__':
    main()  # zazenemo main funkcijo
