# ================================================================
# VAJE 9.4 - Vaja 3: InfluxDB preko Python clienta
# Namesti knjižnico: pip install influxdb matplotlib
# ================================================================

from influxdb import InfluxDBClient
import random
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ----------------------------------------------------------------
# Parametri za povezavo na InfluxDB server
# ----------------------------------------------------------------
HOST = '127.0.0.1'
PORT = 1234
USER = 'guest'
PASSWORD = 'guest'
DB_NAME = 'mojDatabase_python'   # ime svojega database-a

# Ustvari klientov objekt — ta objekt upravljamo za vse operacije
client = InfluxDBClient(HOST, PORT, USER, PASSWORD)


# ================================================================
# (a) Ustvari novi database in ga nastavi kot aktivnega
# ================================================================

# Ustvari database (če že obstaja, ne bo vrnil napake)
client.create_database(DB_NAME)
print(f"[a] Database '{DB_NAME}' ustvarjen.")

# Nastavi ta database kot privzetega za vse nadaljnje operacije
client.switch_database(DB_NAME)
print(f"[a] Aktivni database: {DB_NAME}")

# Grafana: v Grafani ročno dodaj Data source:
#   Type: InfluxDB
#   URL: http://127.0.0.1:1234
#   Database: mojDatabase_python
#   User: guest, Password: guest


# ================================================================
# (b) Direktno vpiši eno točko
# ================================================================

# Vsaka točka je Python slovar z obveznimi polji:
#   "measurement" = ime meritve (kot tabela v SQL)
#   "tags"        = metapodatki za filtriranje (indeksirani)
#   "fields"      = dejanske meritve (vrednosti)
#   "time"        = neobvezen timestamp (ISO format ali epoch)

ena_tocka = [
    {
        "measurement": "Temperature",
        "tags": {
            "user": "student"       # tag za razlikovanje virov
        },
        "fields": {
            "T1": -0.14             # vrednost meritve T1
        }
        # "time" izpustimo → InfluxDB bo dodal trenutni čas
    }
]

client.write_points(ena_tocka)
print(f"[b] Ena točka zapisana: T1=-0.14")


# ================================================================
# (c) Program, ki vsako sekundo pošlje T1, T2, P1, P2
# ================================================================
# Zaženi ta del v ločenem terminalu/kernelu, da teče v ozadju.
# Ustavi z Ctrl+C.

def zacni_posiljanje(stevilo_iteracij=30):
    """
    Vsako sekundo pošlje 4 meritve v InfluxDB:
    - T1, T2 (temperatura) kot en zapis v measurement "Temperature"
    - P1, P2 (pritisk) kot en zapis v measurement "Pressure"
    Vrednosti so naključna števila (simulacija senzorjev).
    """
    print(f"[c] Začenjam pošiljanje podatkov vsako sekundo ({stevilo_iteracij}x)...")

    for i in range(stevilo_iteracij):
        # Generiraj naključne vrednosti (simulacija senzorja)
        t1 = round(random.uniform(18.0, 25.0), 2)   # temperatura med 18-25°C
        t2 = round(random.uniform(18.0, 25.0), 2)
        p1 = round(random.uniform(1010.0, 1020.0), 1)  # pritisk v hPa
        p2 = round(random.uniform(1010.0, 1020.0), 1)

        # Podatki v obliki, ki jo zahteva InfluxDB Python client
        # Oba measurementa pošljemo skupaj v enem klicu write_points
        podatki = [
            {
                "measurement": "Temperature",
                "tags": {"user": "student"},
                "fields": {
                    "T1": t1,
                    "T2": t2
                }
            },
            {
                "measurement": "Pressure",
                "tags": {"user": "student"},
                "fields": {
                    "P1": p1,
                    "P2": p2
                }
            }
        ]

        # Pošlji točke na server
        client.write_points(podatki)
        print(f"  [{i+1}/{stevilo_iteracij}] T1={t1}, T2={t2}, P1={p1}, P2={p2}")

        # Počakaj 1 sekundo pred naslednjim pošiljanjem
        time.sleep(1)

    print("[c] Pošiljanje končano.")

# Zakomentiraj, če ne želiš pošiljati — odkomentiraj za zagon:
# zacni_posiljanje(stevilo_iteracij=30)


# ================================================================
# (d) Pridobi podatke in nariši z matplotlib (pravilna x-os: čas)
# ================================================================

def narisi_podatke():
    """
    Pridobi T1 iz InfluxDB in ga nariše z matplotlib.
    X-os: pravi čas (datetime), Y-os: vrednost meritve.
    """

    # InfluxQL poizvedba — pridobi vse T1 vrednosti iz Temperature meritve
    # "autogen" je privzeta retention policy v InfluxDB
    rezultat = client.query(
        f'SELECT "T1" FROM "{DB_NAME}"."autogen"."Temperature"'
    )

    # get_points() vrne iterator slovarjev: {"time": "...", "T1": vrednost}
    tocke = list(rezultat.get_points())

    if not tocke:
        print("[d] Ni podatkov za risanje. Najprej poženi zacni_posiljanje().")
        return

    # Ločimo čas in vrednosti v dve listi
    casi = []
    vrednosti_t1 = []

    for tocka in tocke:
        # InfluxDB vrne čas kot ISO 8601 string, npr. "2024-01-15T12:30:00Z"
        # Pretvorimo ga v Python datetime objekt za pravilno os
        cas = datetime.strptime(tocka['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        casi.append(cas)
        vrednosti_t1.append(tocka['T1'])

    # Nariši graf z matplotlib
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(casi, vrednosti_t1, 'b-o', markersize=4, label='T1 (°C)')

    # Pravilno formatiraj x-os kot čas
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()   # nagni datumske oznake za boljšo berljivost

    ax.set_xlabel('Čas')
    ax.set_ylabel('Temperatura (°C)')
    ax.set_title('T1 - Temperatura iz InfluxDB')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('temperatura_t1.png', dpi=150)
    plt.show()
    print(f"[d] Graf shranjen kot temperatura_t1.png ({len(tocke)} točk)")

# Zakomentiraj po potrebi:
# narisi_podatke()


# ================================================================
# GLAVNI PROGRAM — poženi vse po vrsti
# ================================================================
if __name__ == '__main__':
    print("=== Vaja 3: InfluxDB Python client ===\n")

    # (b) je že zgoraj (ena točka)

    # (c) Pošlji 10 sekund podatkov
    zacni_posiljanje(stevilo_iteracij=10)

    # (d) Nariši
    narisi_podatke()
