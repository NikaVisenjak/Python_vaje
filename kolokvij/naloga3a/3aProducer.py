import pika   # knjiznica za komunikacijo z RabbitMQ
import time   # za sleep med posiljanjem vprasanj

EXCHANGE = "nagradna_igra"  # ime topic exchange-a na katerega posiljamo vprasanja

# Seznam testnih vprasanj v obliki (routing_key, besedilo)
# routing key format: 'podrocje.podpodrocje.vrsta'
VPRASANJA = [
    ("matematika.algebra.ja_ne",      "Ali je x^2 vedno pozitiven?"),
    ("matematika.geometrija.odprti",  "Koliko kotov ima trikotnik?"),
    ("biologija.deljenje.ja_ne",      "Ali se celice delijo z mitozo?"),
    ("biologija.genetika.ja_ne",      "Ali je DNA dvovijacnica?"),
    ("kemija.anorganska.ja_ne",       "Ali je kemijska formula za vodo H2O?"),
    ("kemija.organska.odprti",        "Kaj je benzen?"),
    ("fizika.mehanika.ja_ne",         "Ali je sila enaka masi krat pospesek?"),
    ("matematika.statistika.odprti",  "Kaj je standardni odklon?"),
    ("biologija.deljenje.odprti",     "Opisi fazo mitoze."),
    ("zgodovina.srednji_vek.ja_ne",   "Ali je bil Karel Veliki cesar?"),
]

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))  # vzpostavimo TCP povezavo z RabbitMQ
    channel = connection.channel()  # odpremo kanal za komunikacijo

    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic')  # deklariramo topic exchange (ce ze obstaja, se ne ustvari znova)
    print(f"Exchange '{EXCHANGE}' pripravljen. Posiljam vprasanja...\n")

    for routing_key, besedilo in VPRASANJA:  # gremo cez vsa testna vprasanja
        channel.basic_publish(
            exchange=EXCHANGE,             # posiljamo na topic exchange (ne direktno v queue)
            routing_key=routing_key,       # RabbitMQ bo na podlagi tega dolocil kateri subscriberji dobijo sporocilo
            body=besedilo.encode('utf-8'), # besedilo vprasanja kot bytes
            properties=pika.BasicProperties(delivery_mode=2)  # persistentno sporocilo
        )
        print(f"[POSLANO] routing_key='{routing_key}' | '{besedilo}'")  # izpisemo poslano vprasanje
        time.sleep(0.5)  # kratka pavza med posiljanjem (da subscriber steze)

    print("\nVsa vprasanja poslana!")  # obvestimo da smo poslali vse
    connection.close()  # zapremo povezavo z RabbitMQ

if __name__ == '__main__':
    main()  # zazenemo main funkcijo