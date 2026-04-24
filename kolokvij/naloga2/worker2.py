import pika  # knjiznica za komunikacijo z RabbitMQ
import time  # za sleep pri cakanju in pri zavracanju nalog
 
RABBITMQ_HOST = 'localhost'  # naslov RabbitMQ streznika
 
# Worker 2 se BOJI stevilke 1.
# Strategija: ce kateri od stevilk je 1, sporocilo zavrne (basic_nack z requeue=True)
# -> RabbitMQ vrne nalogo nazaj v vrsto, kjer jo prevzame Worker 1.
# Tako Worker 2 minimalno vidi stevilko 1, vse naloge pa so vseeno dokoncane!
 
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
    print(f"Worker 2 (strahopetec) - task queue: {task_queue}, result queue: {result_queue}\n")  # izpisemo katera queue-ja bomo uporabljali
 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))  # vzpostavimo TCP povezavo z RabbitMQ
    channel = connection.channel()  # odpremo kanal za komunikacijo
 
    channel.basic_qos(prefetch_count=1)  # fair dispatch: worker dobi novo nalogo sele ko zakljuci prejsnjo
 
    def callback(ch, method, properties, body):  # funkcija se poklic ko prejmemo sporocilo
        msg = body.decode()              # pretvorimo bytes v string npr. "1,3"
        a, b = map(int, msg.split(','))  # razdelimo po vejici in pretvorimo v stevilki
 
        if a == 1 or b == 1:  # ce katera od stevilk je 1 -> Worker 2 se boji!
            print(f"[Worker 2] 😱 Številka 1 zaznana v '{msg}'! Zavračam nalogo!")  # izpisemo da zavracamo
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)  # zavrnemo sporocilo; requeue=True: RabbitMQ ga vrne nazaj v queue (ne izgubi se!)
            time.sleep(0.1)  # kratka pavza, da ima Worker 1 cas prevzeti zavrnjeno nalogo preden jo Worker 2 morda dobi spet
        else:  # stevilke brez enke -> Worker 2 normalno obdela
            rezultat = a * b                 # izracunamo zmnozek
            odgovor = f"{a}x{b}={rezultat}" # sestavimo odgovor npr. "3x5=15"
            print(f"[Worker 2] Obdelano: {msg} -> {odgovor}")  # izpisemo rezultat
 
            ch.basic_publish(
                exchange='',             # prazen exchange = direktno v queue
                routing_key=result_queue,# posljemo v result queue
                body=odgovor.encode(),   # vsebina kot bytes
                properties=pika.BasicProperties(delivery_mode=2)  # persistentno sporocilo
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)  # potrdimo RabbitMQ da smo nalogo uspesno obdelali
 
    channel.basic_consume(queue=task_queue, on_message_callback=callback)  # registriramo callback funkcijo za task_queue
    print("Worker 2 čaka na naloge (brez enk!)...")  # obvestimo da smo pripravljeni
    channel.start_consuming()  # zazenemo blokirajoce cakanje na sporocila (neskoncna zanka)
 
if __name__ == '__main__':
    main()  # zazenemo main funkcijo