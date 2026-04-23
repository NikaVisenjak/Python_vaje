# =============================================================
# Izpit 2 - Naloga 4: Socket komunikacija s CRC16
#
# Protokol (razlika od izpita 1: zadnja 2 bajta sta CRC16):
# 1. Client → Server: 10-bytno obvestilo o velikosti sporočila
# 2. Server → Client: 10-bytno obvestilo o željeni velikosti kosa
# 3. Client → Server: sporočilo po kosih (zadnja 2 bajta = CRC16)
# 4. Server sestavi, preveri CRC16, prikaže sporočilo
#
# CRC16 implementacija (iz http://pinta.ijs.si/crc16.html):
# =============================================================

import socket
import socketserver
import struct

# =============================================================
# CRC16 implementacija (CCITT)
# Vir: http://pinta.ijs.si/crc16.html
# =============================================================
def crc16(data: bytes) -> int:
    """Izračunaj CRC16 za bajte 'data'."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

ZELENA_VELIKOST_KOSA = 32

# ==========================
# SERVER
# ==========================
class CRCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request

        # Korak 1: Prejmi 10-bytni header z velikostjo sporočila
        header = conn.recv(10)
        velikost_sporocila = int(header.decode('utf-8').strip())
        print(f"[Server] Pričakujem {velikost_sporocila} bajtov (skupaj z 2 bajt CRC16).")

        # Korak 2: Pošlji 10-bytni odgovor z željeno velikostjo kosa
        odgovor = str(ZELENA_VELIKOST_KOSA).zfill(10).encode('utf-8')
        conn.sendall(odgovor)

        # Korak 3: Sprejmi celotno sporočilo po kosih
        prejeto = b""
        while len(prejeto) < velikost_sporocila:
            preostalo = velikost_sporocila - len(prejeto)
            kos = conn.recv(min(ZELENA_VELIKOST_KOSA, preostalo))
            if not kos:
                break
            prejeto += kos

        # Korak 4: Ločimo sporočilo in CRC16 (zadnja 2 bajta)
        if len(prejeto) < 2:
            print("[Server] Napaka: sporočilo prekratko.")
            return

        sporocilo_bajti = prejeto[:-2]         # vse razen zadnjih 2 bajtov
        prejeti_crc = struct.unpack('>H', prejeto[-2:])[0]  # zadnja 2 bajta (big-endian)

        # Preveri CRC16
        izracunan_crc = crc16(sporocilo_bajti)

        if izracunan_crc == prejeti_crc:
            print(f"[Server] CRC16 OK (0x{izracunan_crc:04X}). Sporočilo:")
            print(sporocilo_bajti.decode('utf-8'))
        else:
            print(f"[Server] CRC16 NAPAKA! Pričakovan 0x{izracunan_crc:04X}, prejel 0x{prejeti_crc:04X}")

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    with socketserver.TCPServer((HOST, PORT), CRCHandler) as server:
        print(f"[Server] Posluša na {HOST}:{PORT}...")
        server.serve_forever()


# ==========================
# CLIENT
# ==========================
def pošlji_sporocilo(sporocilo: str):
    HOST, PORT = "localhost", 9999

    # Pretvori sporočilo v bajte
    sporocilo_bajti = sporocilo.encode('utf-8')

    # Izračunaj CRC16 celotnega sporočila (brez CRC samega)
    checksum = crc16(sporocilo_bajti)

    # Dodaj CRC16 na konec kot 2 bajta (big-endian)
    data = sporocilo_bajti + struct.pack('>H', checksum)
    velikost = len(data)

    print(f"[Client] Sporočilo: {len(sporocilo_bajti)} bajtov + 2 bajta CRC16 = {velikost} bajtov skupaj.")
    print(f"[Client] CRC16 = 0x{checksum:04X}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        # Korak 1: Pošlji 10-bytni header
        header = str(velikost).zfill(10).encode('utf-8')
        s.sendall(header)

        # Korak 2: Prejmi željeno velikost kosa
        odgovor = s.recv(10)
        velikost_kosa = int(odgovor.decode('utf-8').strip())
        print(f"[Client] Server zahteva kose po {velikost_kosa} bajtov.")

        # Korak 3: Pošlji po kosih
        poslano = 0
        while poslano < velikost:
            kos = data[poslano : poslano + velikost_kosa]
            s.sendall(kos)
            poslano += len(kos)

        print("[Client] Sporočilo poslano.")

if __name__ == '__main__':
    pošlji_sporocilo("Testno sporočilo z CRC16 za izpit avgusta 2024.")
