# =============================================================
# Izpit 1 - Naloga 4: Socket komunikacija s kosanjem sporočila
#
# Protokol:
# 1. Client → Server: 10-bytno obvestilo o velikosti sporočila
# 2. Server → Client: 10-bytno obvestilo o željeni velikosti kosa
# 3. Client → Server: sporočilo po kosih zahtevane velikosti
# 4. Server sestavi sporočilo in ga prikaže (print)
# =============================================================

# ==========================
# SERVER (server.py)
# ==========================
import socketserver

# Izberemo velikost kosa, ki ga server zahteva od klienta
ZELENA_VELIKOST_KOSA = 16  # server želi prejemati po 16 bajtov naenkrat

class SporocilniHandler(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request

        # --- KORAK 1: Prejmi 10-bytni header z velikostjo sporočila ---
        header = conn.recv(10)
        if len(header) < 10:
            print("Napaka: nepopoln header")
            return

        # Pretvori header (10 bajtov) v celo število — velikost sporočila
        velikost_sporocila = int(header.decode('utf-8').strip())
        print(f"[Server] Klient želi poslati {velikost_sporocila} bajtov.")

        # --- KORAK 2: Pošlji 10-bytni odgovor z željeno velikostjo kosa ---
        # Odgovor je 10-bytno število, desno poravnano z ničlami
        odgovor = str(ZELENA_VELIKOST_KOSA).zfill(10).encode('utf-8')
        conn.sendall(odgovor)
        print(f"[Server] Zahtevam kose po {ZELENA_VELIKOST_KOSA} bajtov.")

        # --- KORAK 3: Sprejmi sporočilo po kosih ---
        prejeto = b""
        while len(prejeto) < velikost_sporocila:
            # Preostalo število bajtov za sprejem
            preostalo = velikost_sporocila - len(prejeto)
            # Sprejmi naslednji kos (ne večji od želenega ali preostalega)
            kos = conn.recv(min(ZELENA_VELIKOST_KOSA, preostalo))
            if not kos:
                break  # Povezava zaprta prezgodaj
            prejeto += kos

        # --- KORAK 4: Prikaži sestavljeno sporočilo ---
        print(f"[Server] Sestavljeno sporočilo ({len(prejeto)} bajtov):")
        print(prejeto.decode('utf-8'))

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    # TCPServer sprejema vhodne povezave
    with socketserver.TCPServer((HOST, PORT), SporocilniHandler) as server:
        print(f"[Server] Posluša na {HOST}:{PORT}...")
        server.serve_forever()


# ==========================
# CLIENT (client.py)
# ==========================
import socket

def pošlji_sporocilo(sporocilo: str):
    HOST, PORT = "localhost", 9999

    # Pretvori sporočilo v bajte
    data = sporocilo.encode('utf-8')
    velikost = len(data)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # --- KORAK 1: Pošlji 10-bytni header z velikostjo sporočila ---
        # Velikost zapišemo kot 10-znakovno število z levimi ničlami
        header = str(velikost).zfill(10).encode('utf-8')
        s.sendall(header)
        print(f"[Client] Poslal header: sporočilo ima {velikost} bajtov.")

        # --- KORAK 2: Prejmi 10-bytni odgovor serverja o želenem kosu ---
        odgovor = s.recv(10)
        velikost_kosa = int(odgovor.decode('utf-8').strip())
        print(f"[Client] Server zahteva kose po {velikost_kosa} bajtov.")

        # --- KORAK 3: Pošlji sporočilo po kosih ---
        poslano = 0
        while poslano < velikost:
            # Izreži naslednji kos
            kos = data[poslano : poslano + velikost_kosa]
            s.sendall(kos)
            poslano += len(kos)
            print(f"[Client] Poslal kos {len(kos)} bajtov (skupaj {poslano}/{velikost})")

        print("[Client] Sporočilo v celoti poslano.")

if __name__ == '__main__':
    pošlji_sporocilo("Pozdravljeni! To je testno sporočilo za izpit iz strežniških aplikacij.")
