# =============================================================
# Izpit 3 (september 2024) - Naloga 4: Socket + CRC16 + SSL
#
# Razlike od izpita 2:
# - Header velikosti sporočila: 6 bajtov (ne 10!) kot unsigned int
# - Header želenega kosa: 3 bajte (ne 10!)
# - Certifikati (ssl.wrap_socket)
#
# Protokol:
# 1. Client → Server: 6-bytni uint header z velikostjo sporočila
# 2. Server → Client: 3-bytni uint header z željeno velikostjo kosa
# 3. Client → Server: sporočilo po kosih (zadnja 2 bajta = CRC16)
# 4. Server sestavi, preveri CRC16, prikaže
#
# Za certifikate generiraj samopodpisane certifikate:
#   openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
# =============================================================

import socket
import ssl
import struct
import socketserver

# CRC16 (CCITT)
def crc16(data: bytes) -> int:
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
# SERVER z SSL
# ==========================
class SSLCRCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request  # conn je že SSL socket (ovojimo spodaj)

        # Korak 1: Prejmi 6-bytni unsigned int header z velikostjo sporočila
        # 6 bajtov = do 2^48 ≈ 281 TB — dovolj za vsa sporočila
        header = self._recv_exact(conn, 6)
        # Razpakuj 6-bytni big-endian unsigned int (Python nima 6-byte struct,
        # zato preberemo kot 8-byte in odštejemo 2 bajta levo)
        velikost_sporocila = int.from_bytes(header, byteorder='big')
        print(f"[Server] Pričakujem {velikost_sporocila} bajtov skupaj (z CRC16).")

        # Korak 2: Pošlji 3-bytni header z željeno velikostjo kosa
        odgovor = ZELENA_VELIKOST_KOSA.to_bytes(3, byteorder='big')
        conn.sendall(odgovor)

        # Korak 3: Sprejmi vse podatke
        prejeto = b""
        while len(prejeto) < velikost_sporocila:
            preostalo = velikost_sporocila - len(prejeto)
            kos = conn.recv(min(ZELENA_VELIKOST_KOSA, preostalo))
            if not kos:
                break
            prejeto += kos

        # Korak 4: Preveri CRC16
        sporocilo_bajti = prejeto[:-2]
        prejeti_crc = struct.unpack('>H', prejeto[-2:])[0]
        izracunan_crc = crc16(sporocilo_bajti)

        if izracunan_crc == prejeti_crc:
            print(f"[Server] CRC16 OK. Sporočilo: {sporocilo_bajti.decode('utf-8')}")
        else:
            print(f"[Server] CRC16 NAPAKA!")

    def _recv_exact(self, conn, n):
        """Prejmi natanko n bajtov."""
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                break
            buf += chunk
        return buf

def serve():
    HOST, PORT = "localhost", 9999

    # Ustvari SSL kontekst za server
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain('server.crt', 'server.key')  # certifikat in zasebni ključ

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        print(f"[Server] SSL server posluša na {HOST}:{PORT}...")

        with ssl_context.wrap_socket(sock, server_side=True) as ssl_sock:
            while True:
                conn, addr = ssl_sock.accept()
                print(f"[Server] Povezava od {addr}")
                handler = SSLCRCHandler(conn, addr, None)
                handler.handle()
                conn.close()


# ==========================
# CLIENT z SSL
# ==========================
def pošlji_sporocilo(sporocilo: str):
    HOST, PORT = "localhost", 9999

    sporocilo_bajti = sporocilo.encode('utf-8')
    checksum = crc16(sporocilo_bajti)

    # Sporočilo + 2 bajta CRC16
    data = sporocilo_bajti + struct.pack('>H', checksum)
    velikost = len(data)

    # Ustvari SSL kontekst za klienta
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # Za samopodpisane certifikate: naloži CA certifikat
    ssl_context.load_verify_locations('server.crt')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with ssl_context.wrap_socket(sock, server_hostname=HOST) as ssl_sock:
            ssl_sock.connect((HOST, PORT))

            # Korak 1: Pošlji 6-bytni header
            header = velikost.to_bytes(6, byteorder='big')
            ssl_sock.sendall(header)
            print(f"[Client] Poslal 6-bytni header: {velikost} bajtov.")

            # Korak 2: Prejmi 3-bytni header
            odgovor = ssl_sock.recv(3)
            velikost_kosa = int.from_bytes(odgovor, byteorder='big')
            print(f"[Client] Server zahteva kose po {velikost_kosa} bajtov.")

            # Korak 3: Pošlji po kosih
            poslano = 0
            while poslano < velikost:
                kos = data[poslano : poslano + velikost_kosa]
                ssl_sock.sendall(kos)
                poslano += len(kos)

            print("[Client] Sporočilo poslano.")

if __name__ == '__main__':
    pošlji_sporocilo("SSL testno sporočilo za izpit september 2024.")
