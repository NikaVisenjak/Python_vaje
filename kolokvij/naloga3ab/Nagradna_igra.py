import pika  # knjiznica za komunikacijo z RabbitMQ

IME_PRIIMEK = "Ime Priimek"          # TODO: zamenjaj s svojim imenom in priimkom
EXCHANGE = "nagradna_igra"           # ime exchange-a na katerega smo vezani (topic exchange)
RESULT_QUEUE = f"{IME_PRIIMEK} znam" # ime queue-ja kamor posiljamo odgovore

# Zelimo odgovarjati SAMO na vprasanja kjer:
#   1. podrocje == "matematika"            (karkoli.karkoli)
#   2. podrocje == "biologija" IN podpodrocje == "deljenje"
#   3. vrsta == "ja_ne"                    (karkoli.karkoli.ja_ne)
#
# Binding keys za topic exchange:
#   "#"        ujema 0 ali vec besed (poljubna pot)
#   "*"        ujema tocno eno besedo
#
#   matematika.#       -> vse iz matematike
#   biologija.deljenje.* -> biologija + deljenje + karkoli vrsta
#   #.ja_ne            -> karkoli + ja_ne kot vrsta

BINDING_KEYS = [
    "matematika.#",        # vse kategorije in vrste iz matematike
    "biologija.deljenje.*",# biologija, podpodrocje deljenje, vrsta je karkoli
    "#.ja_ne",             # katerokoli podrocje in podpodrocje, vrsta = ja_ne
]

def se_ujema(routing_key: str) -> bool:
    """
    Dodatna preveritev: ker '#.ja_ne' ujame tudi 'matematika.x.ja_ne',
    ki bi ga ze ujel 'matematika.#', je logika ze pokrita z binding keys.
    Ta funkcija je tu za dokumentacijo - RabbitMQ binding keys ze naredijo
    pravilno filtriranje, zato vedno vrnemo True (ce smo sporocilo dobili,
    pomeni da se ujema z vsaj enim binding key-em).
    """
    return True  # RabbitMQ je ze preveril binding keys, sporocilo je relevantno

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))  # vzpostavimo TCP povezavo z RabbitMQ
    channel = connection.channel()  # odpremo kanal za komunikacijo

    channel.exchange_declare(exchange=EXCHANGE, exchange_type='topic')  # deklariramo topic exchange (ce ze obstaja, se ne ustvari znova)

    # Ustvarimo ekskluzivni queue z nakljucnim imenom za prejemanje vprasanj
    queue_result = channel.queue_declare(queue='', exclusive=True)  # exclusive=True: queue se izbrise ko se povezava zapre
    my_queue = queue_result.method.queue  # preberemo nakljucno ime, ki ga je dodelil RabbitMQ
    print(f"Moj queue za sprejemanje vprasanj: {my_queue}")

    # Vezemo queue na exchange za vsak binding key posebej
    for binding_key in BINDING_KEYS:
        channel.queue_bind(
            exchange=EXCHANGE,      # exchange na katerega se vezemo
            queue=my_queue,         # nas lokalni queue
            routing_key=binding_key # vzorec po katerem filtriramo sporocila
        )
        print(f"  Vezano na: {binding_key}")  # izpisemo vsak binding key

    print(f"\nPoslusalec zagnan. Odgovori gredo v queue: '{RESULT_QUEUE}'\n")

    def callback(ch, method, properties, body):  # funkcija se poklic ko prejmemo vprasanje
        routing_key = method.routing_key  # preberemo routing key sporocila npr. "matematika.algebra.ja_ne"
        vprasanje = body.decode('utf-8')  # dekodiramo besedilo vprasanja

        print(f"[PREJETO] routing_key='{routing_key}' | '{vprasanje}'")  # izpisemo prejeto vprasanje

        # Ce smo sporocilo dobili, MORAMO odgovoriti (ker smo ga dejansko prebrali)
        ch.basic_publish(
            exchange='',          # direktno v queue (default exchange)
            routing_key=RESULT_QUEUE,  # ime queue-ja "Ime Priimek znam"
            body=vprasanje.encode('utf-8'),  # posredujemo enako besedilo kot vprasanje
            properties=pika.BasicProperties(delivery_mode=2)  # persistentno sporocilo
        )
        print(f"[ODGOVORJENO] -> '{RESULT_QUEUE}': '{vprasanje}'\n")  # potrdimo da smo odgovorili

        ch.basic_ack(delivery_tag=method.delivery_tag)  # potrdimo RabbitMQ da smo sporocilo uspesno obdelali

    channel.basic_qos(prefetch_count=1)  # fair dispatch: prejmemo eno vprasanje naenkrat (hitrejsi odziv)
    channel.basic_consume(queue=my_queue, on_message_callback=callback)  # registriramo callback za nas queue
    channel.start_consuming()  # zazenemo blokirajoce cakanje na sporocila (neskoncna zanka)

if __name__ == '__main__':
    main()  # zazenemo main funkcijo