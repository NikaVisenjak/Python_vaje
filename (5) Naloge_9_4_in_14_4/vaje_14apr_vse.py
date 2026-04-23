# ================================================================
# VAJE 14.4 - InfluxDB: WHERE poizvedbe in Tags
# Namesti: pip install influxdb matplotlib
# ================================================================

from influxdb import InfluxDBClient
import random
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# --- Parametri za povezavo ---
HOST = '127.0.0.1'
PORT = 1234
USER = 'guest'
PASSWORD = 'guest'
DB_NAME = 'mojDatabase_14apr'

# Ustvari klienta in nastavi database
client = InfluxDBClient(HOST, PORT, USER, PASSWORD)
client.create_database(DB_NAME)
client.switch_database(DB_NAME)


# ================================================================
# VAJA 1: Ustvari database in pošiljaj točke vsako sekundo
# ================================================================
# En measurement "Meritev", dva fielda "vrednost_A" in "vrednost_B",
# tag "user" z vrednostma "user1" in "user2" (izmenično).

def vaja1_posiljaj_tocke(stevilo=60):
    """
    Vsako sekundo pošlje eno točko v InfluxDB.
    Tag "user" se izmenjuje med "user1" in "user2",
    kar bo koristno pri Vaji 3 (filtriranje po tagu).
    """
    print(f"[Vaja 1] Pošiljam {stevilo} točk...")

    for i in range(stevilo):
        # Izmenjujemo tag user1/user2 vsako iteracijo
        user_tag = "user1" if i % 2 == 0 else "user2"

        # Naključne vrednosti — pozitivne in negativne (koristno za Vajo 2c)
        val_a = round(random.uniform(-5.0, 10.0), 2)
        val_b = round(random.uniform(-5.0, 10.0), 2)

        tocka = [
            {
                "measurement": "Meritev",
                "tags": {
                    "user": user_tag    # tag za razlikovanje med user1 in user2
                },
                "fields": {
                    "vrednost_A": val_a,
                    "vrednost_B": val_b
                }
                # time izpustimo → server doda trenutni čas
            }
        ]

        client.write_points(tocka)
        print(f"  [{i+1}] user={user_tag}, A={val_a}, B={val_b}")
        time.sleep(1)

    print("[Vaja 1] Pošiljanje končano.\n")


# ================================================================
# VAJA 2: WHERE poizvedbe
# ================================================================

def narisi_graf(casi, vrednosti, naslov, ylabel, barva='b'):
    """Pomožna funkcija za risanje časovnih vrst z matplotlib."""
    if not casi:
        print(f"  [OPOZORILO] Ni podatkov za: {naslov}")
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(casi, vrednosti, f'{barva}-o', markersize=4, label=ylabel)

    # Pravilna x-os: pretvorimo string timestamps v datetime objekte
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.set_xlabel('Čas')
    ax.set_ylabel(ylabel)
    ax.set_title(naslov)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def preberi_in_narisi(query_string, naslov, ylabel, barva='b'):
    """Izvede poizvedbo in nariše rezultat."""
    rezultat = client.query(query_string)
    tocke = list(rezultat.get_points())

    # Preberi čas in vrednost iz vsake točke
    casi = []
    vrednosti = []
    for t in tocke:
        try:
            # Poskusi oba možna formata timestamps (z ali brez mikrosekund)
            cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%SZ')
        casi.append(cas)
        vrednosti.append(list(t.values())[1])  # druga vrednost = field

    narisi_graf(casi, vrednosti, naslov, ylabel, barva)
    return tocke


# ----------------------------------------------------------------
# (a) narisi_zadnjo_minuto — WHERE time >= now() - 1m
# ----------------------------------------------------------------
def narisi_zadnjo_minuto(database, measurement, field):
    """
    Nariše zadnjo minuto podatkov za izbrani field iz measurement.
    WHERE time >= now() - 1m → InfluxDB vrne samo podatke iz zadnje minute.
    """
    # now() = trenutni čas na strežniku
    # 1m    = 1 minuta (InfluxDB duration literal)
    query = (
        f'SELECT "{field}" FROM "{database}"."autogen"."{measurement}" '
        f'WHERE time >= now() - 1m'
    )
    print(f"[2a] Query: {query}")
    return preberi_in_narisi(
        query,
        naslov=f'{field} — zadnja minuta',
        ylabel=field,
        barva='b'
    )


# ----------------------------------------------------------------
# (b) narisi_predzadnjo_minuto — WHERE time >= now()-2m AND time < now()-1m
# ----------------------------------------------------------------
def narisi_predzadnjo_minuto(database, measurement, field):
    """
    Nariše predzadnjo minuto (od 2 do 1 minuto nazaj).
    Uporabimo WHERE ... AND ... za definiranje časovnega okna.
    """
    # AND kombinira dva pogoja: od 2 min do 1 min nazaj
    query = (
        f'SELECT "{field}" FROM "{database}"."autogen"."{measurement}" '
        f'WHERE time >= now() - 2m AND time < now() - 1m'
    )
    print(f"[2b] Query: {query}")
    return preberi_in_narisi(
        query,
        naslov=f'{field} — predzadnja minuta',
        ylabel=field,
        barva='g'
    )


# ----------------------------------------------------------------
# (c) narisi_vecje_od_nic — WHERE field > 0
# ----------------------------------------------------------------
def narisi_vecje_od_nic(database, measurement, field):
    """
    Nariše samo vrednosti, ki so VEČJE od 0.
    WHERE "field" > 0 filtrira negativne in ničelne vrednosti.
    OPOMBA: V InfluxDB moramo pri field filtrih uporabiti narekovaje!
    """
    # Primerjava vrednosti fielda — sintaksa: WHERE "ime_fielda" > stevilo
    query = (
        f'SELECT "{field}" FROM "{database}"."autogen"."{measurement}" '
        f'WHERE "{field}" > 0'
    )
    print(f"[2c] Query: {query}")
    return preberi_in_narisi(
        query,
        naslov=f'{field} > 0 (samo pozitivne vrednosti)',
        ylabel=field,
        barva='r'
    )


# ================================================================
# VAJA 3: Tags — 3 načini filtriranja po tagu
# ================================================================

# ----------------------------------------------------------------
# (a) narisi_od_tag — GROUP BY tag, nato filtriraj v Pythonu
# ----------------------------------------------------------------
def narisi_od_tag(database, measurement, field, tag: dict):
    """
    Nariše time series za specifičen tag.
    tag = slovar, npr. {"user": "user1"}

    Metoda: GROUP BY tag_key → poizvedba vrne ločene serije za vsak tag.
    Nato v Pythonu izberemo samo željeno serijo z result.items().
    """
    # Pridobi ime in vrednost taga iz slovarja
    tag_key = list(tag.keys())[0]       # npr. "user"
    tag_value = list(tag.values())[0]   # npr. "user1"

    # GROUP BY "tag_key" → InfluxDB vrne ločene time series za vsak tag
    query = (
        f'SELECT "{field}" FROM "{database}"."autogen"."{measurement}" '
        f'GROUP BY "{tag_key}"'
    )
    print(f"[3a] Query: {query}")
    rezultat = client.query(query)

    casi, vrednosti = [], []

    # result.items() vrne seznam (measurement, tags, points) trojk
    for (name, tags), points in rezultat.items():
        # Filtriramo samo željeni tag value
        if tags.get(tag_key) == tag_value:
            for t in points:
                try:
                    cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%SZ')
                casi.append(cas)
                vrednosti.append(t[field])

    narisi_graf(
        casi, vrednosti,
        naslov=f'{field} — tag {tag_key}={tag_value} (GROUP BY)',
        ylabel=field, barva='b'
    )


# ----------------------------------------------------------------
# (b) SELECT * — pridobi vse fielde in tage, filtriraj v Pythonu
# ----------------------------------------------------------------
def narisi_od_tag_select_star(database, measurement, field, tag: dict):
    """
    SELECT * vrne VSE fielde in tage za vsako točko.
    Nato v Pythonu ručno filtriramo po tagu.

    Slabost: prenos vseh podatkov (nepotrebno pri velikih bazah).
    """
    tag_key = list(tag.keys())[0]
    tag_value = list(tag.values())[0]

    # SELECT * vrne vse stolpce vključno s tagi
    query = (
        f'SELECT * FROM "{database}"."autogen"."{measurement}"'
    )
    print(f"[3b] Query (SELECT *): {query}")
    rezultat = client.query(query)

    casi, vrednosti = [], []
    for t in rezultat.get_points():
        # Filtriraj po tagu v Pythonu (ne v query-ju)
        if t.get(tag_key) == tag_value:
            try:
                cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                cas = datetime.strptime(t['time'], '%Y-%m-%dT%H:%M:%SZ')
            casi.append(cas)
            vrednosti.append(t[field])

    narisi_graf(
        casi, vrednosti,
        naslov=f'{field} — tag {tag_key}={tag_value} (SELECT *)',
        ylabel=field, barva='g'
    )


# ----------------------------------------------------------------
# (c) WHERE tag = 'vrednost' — direktno filtriranje v query-ju ✓
# ----------------------------------------------------------------
def narisi_od_tag_direktno(database, measurement, field, tag: dict):
    """
    Najboljša metoda: filtriranje taga direktno v InfluxQL query-ju z WHERE.
    Query vrne SAMO relevantne podatke → minimalen prenos podatkov.

    PRIPOROČENA METODA: ker je najučinkovitejša — filter se izvede
    na strežniku, ne v Pythonu.
    """
    tag_key = list(tag.keys())[0]
    tag_value = list(tag.values())[0]

    # WHERE "tag_key" = 'tag_value' — tagi se filtrirajo z enojnimi narekovaji!
    # (fieldi z dvojnimi, tagi z enojnimi — InfluxDB razlikuje med njima)
    query = (
        f'SELECT "{field}" FROM "{database}"."autogen"."{measurement}" '
        f'WHERE "{tag_key}" = \'{tag_value}\''
    )
    print(f"[3c] Query (direktno): {query}")
    return preberi_in_narisi(
        query,
        naslov=f'{field} — tag {tag_key}={tag_value} (WHERE direktno)',
        ylabel=field, barva='r'
    )

# ----------------------------------------------------------------
# Priporočilo: Metoda (c) — WHERE direktno v query-ju
# Razlog:
#   (a) GROUP BY prenese vse serije, filtriranje je v Pythonu
#   (b) SELECT * prenese VSE fielde in tage — zelo potratno
#   (c) WHERE filtrira na strežniku → najmanj prenosa podatkov,
#       najhitrejše, najbolj skalabilno pri velikih bazah
# ----------------------------------------------------------------


# ================================================================
# GLAVNI PROGRAM
# ================================================================
if __name__ == '__main__':
    print("=== Vaje 14.4: WHERE in Tags ===\n")

    # Vaja 1: Najprej pošlji podatke (vsaj 2 minuti za WHERE teste)
    print("--- Vaja 1: Pošiljanje podatkov (2 minuti) ---")
    vaja1_posiljaj_tocke(stevilo=120)

    # Vaja 2: WHERE poizvedbe
    print("\n--- Vaja 2a: Zadnja minuta ---")
    narisi_zadnjo_minuto(DB_NAME, 'Meritev', 'vrednost_A')

    print("\n--- Vaja 2b: Predzadnja minuta ---")
    narisi_predzadnjo_minuto(DB_NAME, 'Meritev', 'vrednost_A')

    print("\n--- Vaja 2c: Samo vrednosti > 0 ---")
    narisi_vecje_od_nic(DB_NAME, 'Meritev', 'vrednost_A')

    # Vaja 3: Tags
    tag = {"user": "user1"}

    print("\n--- Vaja 3a: GROUP BY ---")
    narisi_od_tag(DB_NAME, 'Meritev', 'vrednost_A', tag)

    print("\n--- Vaja 3b: SELECT * ---")
    narisi_od_tag_select_star(DB_NAME, 'Meritev', 'vrednost_A', tag)

    print("\n--- Vaja 3c: WHERE direktno (PRIPOROČENO) ---")
    narisi_od_tag_direktno(DB_NAME, 'Meritev', 'vrednost_A', tag)
