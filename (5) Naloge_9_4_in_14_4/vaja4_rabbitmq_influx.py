# ================================================================
# VAJE 9.4 - Vaja 4: RabbitMQ → InfluxDB → Grafana
#
# Arhitektura:
#   [producer.py]  vsako sekundo pošlje meritev v RabbitMQ queue
#   [consumer.py]  bere iz queue in zapisuje v InfluxDB
#   [Grafana]      prikazuje podatke iz InfluxDB v realnem času
#
# Namesti: pip install pika influxdb
# RabbitMQ server: 127.0.0.1 (privzeti port 5672)
# ================================================================


# ================================================================
# DATOTEKA 1: producer.py
# Zaženi v prvem terminalu: python producer.py
# ================================================================

import pika          # Python knjižnica za RabbitMQ
import json
import random
import time

# --- Parametri RabbitMQ ---
RABBITMQ_HOST = '127.0.0.1'
QUEUE_NAME = 'meritve'   # ime queue-a — producer in consumer morata imeti enako

def zacni_producer():
    """
    Vsako sekundo pošlje JSON sporočilo z meritvami v RabbitMQ queue.
    Sporočilo vsebuje T1, T2 (temperatura) in P1, P2 (pritisk).
    """

    # Vzpostavi TCP povezavo z RabbitMQ strežnikom
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )

    # Channel je virtualni kanal znotraj povezave (lahkotni objekt)
    channel = connection.channel()

    # Deklariraj queue — če ne obstaja, ga ustvari.
    # durable=True pomeni, da queue preživi restart RabbitMQ serverja
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    print(f"[Producer] Pošiljam v queue '{QUEUE_NAME}' vsako sekundo...")

    try:
        while True:
            # Sestavi sporočilo kot Python slovar
            sporocilo = {
                "measurement": "Temperature",
                "tags": {"user": "student"},
                "fields": {
                    "T1": round(random.uniform(18.0, 25.0), 2),
                    "T2": round(random.uniform(18.0, 25.0), 2),
                    "P1": round(random.uniform(1010.0, 1020.0), 1),
                    "P2": round(random.uniform(1010.0, 1020.0), 1)
                }
            }

            # Pretvori slovar v JSON string za pošiljanje
            body = json.dumps(sporocilo)

            # Pošlji sporočilo v queue
            # exchange=''        → privzeti exchange (direct delivery)
            # routing_key        → ime queue-a, kamor gre sporočilo
            # body               → vsebina sporočila (bytes ali string)
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2  # 2 = persistent (sporočilo preživi restart)
                )
            )

            print(f"[Producer] Poslano: {sporocilo['fields']}")
            time.sleep(1)   # počakaj sekundo

    except KeyboardInterrupt:
        print("\n[Producer] Ustavljen (Ctrl+C).")
    finally:
        connection.close()

if __name__ == '__main__':
    zacni_producer()


# ================================================================
# DATOTEKA 2: consumer.py
# Zaženi v DRUGEM terminalu: python consumer.py
# ================================================================

import pika
import json
from influxdb import InfluxDBClient

# --- Parametri RabbitMQ ---
RABBITMQ_HOST = '127.0.0.1'
QUEUE_NAME = 'meritve'

# --- Parametri InfluxDB ---
INFLUX_HOST = '127.0.0.1'
INFLUX_PORT = 8086
INFLUX_USER = 'guest'
INFLUX_PASSWORD = 'guest'
INFLUX_DB = 'mojDatabase_rabbitmq'

def zacni_consumer():
    """
    Posluša RabbitMQ queue in vsako prejeto sporočilo zapiše v InfluxDB.
    Deluje dokler ga ne ustaviš s Ctrl+C.
    """

    # Poveži se na InfluxDB in ustvari database, če ne obstaja
    influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD)
    influx_client.create_database(INFLUX_DB)
    influx_client.switch_database(INFLUX_DB)
    print(f"[Consumer] Povezan na InfluxDB, database: {INFLUX_DB}")

    # Poveži se na RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    # Deklariraj isti queue (idempotentno — če že obstaja, ne bo napake)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def callback(ch, method, properties, body):
        """
        Ta funkcija se pokliče za vsako sporočilo iz queue-a.
        ch         = channel objekt
        method     = metapodatki dostave (npr. delivery_tag)
        properties = lastnosti sporočila
        body       = vsebina sporočila (bytes)
        """

        # Dekodiraj JSON sporočilo iz bytov
        podatki = json.loads(body.decode('utf-8'))
        print(f"[Consumer] Prejeto: {podatki['fields']}")

        # Pripravi točko za InfluxDB (isti format kot v Vaji 3)
        tocka = [
            {
                "measurement": podatki["measurement"],
                "tags": podatki["tags"],
                "fields": {
                    "T1": podatki["fields"]["T1"],
                    "T2": podatki["fields"]["T2"]
                }
            },
            {
                "measurement": "Pressure",
                "tags": podatki["tags"],
                "fields": {
                    "P1": podatki["fields"]["P1"],
                    "P2": podatki["fields"]["P2"]
                }
            }
        ]

        # Zapiši v InfluxDB
        influx_client.write_points(tocka)
        print(f"[Consumer] Zapisano v InfluxDB.")

        # Potrdi prejem sporočila (acknowledgment)
        # Brez tega bi RabbitMQ mislil, da sporočilo ni bilo obdelano
        # in bi ga ponovno poslal po reconnectu
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # Nastavi consumer — basic_consume registrira callback funkcijo
    # auto_ack=False → ručno potrjujemo (varnejše)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False
    )

    print(f"[Consumer] Poslušam queue '{QUEUE_NAME}'... (Ctrl+C za ustavitev)")

    try:
        # Vstopi v zanko čakanja na sporočila (blokirajoča)
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[Consumer] Ustavljen.")
        channel.stop_consuming()
    finally:
        connection.close()
        influx_client.close()

if __name__ == '__main__':
    zacni_consumer()
