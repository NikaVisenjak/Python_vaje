# =============================================================
# IZPITI 4, 5, 6 — Skupne naloge
# =============================================================

# =============================================================
# NALOGA 1: ECC simboli — določitev optimalne vrednosti
#
# Imamo klient in server, ki komunicirata po zašumljenem kanalu.
# Knjižnica popravlja napake z ECC (Error Correcting Codes).
# Popraviti zna največ ecc_symbols/2 bajtov napak.
# Cilj: z binarno strategijo najdi MINIMALNI ecc_symbols, ki
# zagotavlja zanesljivo komunikacijo.
# =============================================================

import requests  # knjižnica za klic REST API
import random
import math

# API dostopen na: http://pinta.ijs.si/rssa/static/openapi.yaml
API_BASE = "http://pinta.ijs.si/rssa"

def encode_message(message: bytes, ecc_symbols: int) -> bytes:
    """Pokliče API za enkodiranje sporočila z ECC."""
    response = requests.post(f"{API_BASE}/encode", json={
        "data": message.hex(),
        "ecc_symbols": ecc_symbols
    })
    return bytes.fromhex(response.json()["encoded"])

def decode_message(encoded: bytes, ecc_symbols: int) -> bytes:
    """Pokliče API za dekodiranje in popravljanje sporočila."""
    response = requests.post(f"{API_BASE}/decode", json={
        "data": encoded.hex(),
        "ecc_symbols": ecc_symbols
    })
    result = response.json()
    if result.get("success"):
        return bytes.fromhex(result["decoded"])
    return None  # Ni uspelo popraviti

def simulate_noise(data: bytes, error_rate: float) -> bytes:
    """Simulira zašumljen kanal — naključno pokvari bite."""
    data_list = bytearray(data)
    for i in range(len(data_list)):
        if random.random() < error_rate:
            data_list[i] ^= random.randint(1, 255)  # XOR z naključnim bytom
    return bytes(data_list)

def determine_optimal_ecc(test_message: bytes, error_rate: float, num_tests: int = 10) -> int:
    """
    Z binarno strategijo poišče minimalni ecc_symbols, ki zagotavlja
    zanesljivo komunikacijo pri dani stopnji napak.
    
    Binarno iskanje: testiramo vrednosti 2, 4, 8, 16... dokler ne najdemo
    meje med delujočim in nedelujočim, nato binarno zoožimo interval.
    """
    
    def test_ecc_value(ecc: int) -> bool:
        """Vrni True, če ecc_symbols ZADOSTUJE za popravilo napak."""
        for _ in range(num_tests):
            encoded = encode_message(test_message, ecc)
            noisy = simulate_noise(encoded, error_rate)
            decoded = decode_message(noisy, ecc)
            if decoded is None or decoded != test_message:
                return False  # Ni uspelo — ecc premajhen
        return True

    # Faza 1: Najdi zgornjo mejo — podvajaj ecc_symbols dokler ne deluje
    ecc = 2
    while not test_ecc_value(ecc):
        ecc *= 2  # Podvoji (eksponentno raste)
        if ecc > 255:
            raise ValueError("Kanal je preveč zašumljen!")
    
    # Faza 2: Binarno iskanje med ecc//2 (ne deluje) in ecc (deluje)
    low = ecc // 2
    high = ecc
    
    while low < high - 1:
        mid = (low + high) // 2
        if test_ecc_value(mid):
            high = mid   # mid deluje → poskusi manjšo vrednost
        else:
            low = mid    # mid ne deluje → zvišaj spodnjo mejo
    
    return high  # Minimalna vrednost, ki deluje

# Primer uporabe:
# optimal = determine_optimal_ecc(b"Testno sporocilo", error_rate=0.05)
# print(f"Optimalni ecc_symbols: {optimal}")


# =============================================================
# NALOGA 2: Nezanesljiva workerja — minimalne re-transmissions
#
# Imamo 2 workerja, vsak zavrne določene naloge (ne vemo vnaprej katere).
# Rešitev: poskusi pri workerju 1, če zavrne → worker 2, in obratno.
# Ko ugotovimo pattern, ga zapomnimo → 0 nepotrebnih ponovnih pošiljanj.
# =============================================================

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any

class SmartTaskDispatcher:
    """
    Pametni razdeljevalec nalog z minimalnimi re-transmissions.
    Uči se, katere naloge vsak worker zavrača, in si to zapomni.
    """
    
    def __init__(self, worker1_fn: Callable, worker2_fn: Callable):
        self.workers = [worker1_fn, worker2_fn]
        
        # Spomin: za vsako nalogo tipa → kateri worker jo sprejme
        # Ključ: tip/hash naloge, vrednost: indeks workerja (0 ali 1)
        self.task_preference = {}
        
        self.total_transmissions = 0
        self.retransmissions = 0

    def submit(self, task: Any) -> Any:
        """
        Pošlji nalogo na workerja z minimalnimi ponovitvami.
        Začni pri workerju, ki je nazadnje uspešno obdelal ta tip naloge.
        """
        task_type = type(task).__name__  # Tip naloge kot ključ

        # Določi vrstni red workerjev glede na pretekle izkušnje
        if task_type in self.task_preference:
            # Začni pri preferiranem workerju
            preferred = self.task_preference[task_type]
            order = [preferred, 1 - preferred]
        else:
            # Prvič — začni pri workerju 0
            order = [0, 1]

        for worker_idx in order:
            self.total_transmissions += 1
            if worker_idx > 0:
                self.retransmissions += 1  # To je re-transmission

            try:
                result = self.workers[worker_idx](task)
                
                # Zapomni si, da ta tip naloge gre k temu workerju
                self.task_preference[task_type] = worker_idx
                return result
                
            except Exception as e:
                # Worker je nalogo zavrnil → poskusi z naslednjim
                print(f"[Dispatcher] Worker {worker_idx} zavrnil nalogo: {e}")
                continue

        raise RuntimeError(f"Oba workerja sta zavrnila nalogo: {task}")

    def stats(self):
        print(f"Skupaj transmissions: {self.total_transmissions}")
        print(f"Re-transmissions: {self.retransmissions}")


# =============================================================
# NALOGA 3: gRPC brez SSL → varnost z lastnim protokolom
#
# Klient in server se identificirata z digitalnim podpisom.
# Identiteta klienta je šifrirana (ne javno dostopna).
#
# Protokol:
# 1. Server pošlje javni ključ klientu (v plaintext — to je OK)
# 2. Klient generira simetrični ključ, ga šifrira s serverjevim javnim ključem
# 3. Vsa nadaljnja komunikacija je AES šifrirana
# 4. Identiteta klienta je šifrirana z AES ključem → ni javno dostopna
# =============================================================

# ---- secure.proto ----
# syntax = "proto3";
#
# service SecureService {
#   rpc Handshake (HandshakeRequest) returns (HandshakeResponse);
#   rpc SecureCall (EncryptedMessage) returns (EncryptedMessage);
# }
#
# message HandshakeRequest {
#   bytes server_public_key_request = 1;   // prazen — zahteva ključ
# }
# message HandshakeResponse {
#   bytes server_public_key = 1;           // RSA javni ključ serverja
# }
# message EncryptedMessage {
#   bytes encrypted_session_key = 1;  // AES ključ, šifriran z RSA
#   bytes encrypted_payload = 2;      // vsebina, šifrirana z AES
#   bytes iv = 3;                     // inicializacijski vektor za AES
# }

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class SecureServicer:
    def __init__(self):
        # Server generira RSA par ključev ob zagonu
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def get_public_key_bytes(self) -> bytes:
        """Vrni javni ključ kot PEM bajte (za pošiljanje klientu)."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def decrypt_with_private_key(self, encrypted: bytes) -> bytes:
        """Dešifriraj z zasebnim ključem (za prejem AES ključa od klienta)."""
        return self.private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt_aes(self, key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
        """Dešifriraj sporočilo z AES-CBC."""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        # Odstrani PKCS7 padding
        pad_len = padded[-1]
        return padded[:-pad_len]


def encrypt_for_server(server_pub_key_pem: bytes, message: bytes, client_identity: str):
    """
    Klient šifrira sporočilo za server:
    1. Generira naključni AES ključ
    2. Šifrira AES ključ z RSA javnim ključem serverja
    3. Šifrira (identity + message) z AES
    
    Identiteta klienta je VEDNO šifrirana → ni javno dostopna!
    """
    # Naloži javni ključ serverja
    public_key = serialization.load_pem_public_key(server_pub_key_pem)
    
    # Generiraj naključni AES-256 ključ in IV
    aes_key = os.urandom(32)
    iv = os.urandom(16)
    
    # Šifriraj payload = identity + "|" + message
    payload = f"{client_identity}|{message.decode('utf-8')}".encode('utf-8')
    
    # PKCS7 padding
    pad_len = 16 - (len(payload) % 16)
    payload += bytes([pad_len] * pad_len)
    
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_payload = encryptor.update(payload) + encryptor.finalize()
    
    # Šifriraj AES ključ z RSA
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    return encrypted_key, encrypted_payload, iv


# =============================================================
# NALOGA 4: Master → 2 slave noda, preverjanje ujemanja
#
# Master pošilja besedila obema slavoma.
# Slave-a morata zagotoviti, da sta prejela ENAKO besedilo.
# Če nista enaka, oba zavržeta.
# Optimalna komunikacija: slave-a si izmenjata samo HASH,
# ne celotnega besedila (hash je majhen, besedila so velika)!
# =============================================================

import hashlib
import grpc
# Predpostavimo ustrezne proto definicije

# ---- sync.proto ----
# syntax = "proto3";
# service SlaveSync {
#   rpc CompareHash (HashMessage) returns (HashMatch);
# }
# message HashMessage { string hash = 1; }
# message HashMatch { bool match = 1; }

class SlaveNode:
    """
    Slave node, ki prejema besedila od masterja in
    preverja ujemanje s sosednjim slave nodom.
    """
    
    def __init__(self, node_id: int, peer_address: str):
        self.node_id = node_id
        self.peer_address = peer_address  # naslov drugega slave noda
        self.current_text = None
        self.current_hash = None

    def receive_text(self, text: str) -> bool:
        """
        Sprejemi besedilo od masterja.
        Vrni True, če se hash ujema s peer slave nodom.
        """
        self.current_text = text
        
        # Izračunaj SHA-256 hash prejetega besedila
        # SHA-256 je dovolj kratek za primerjavo (32 bajtov = 64 hex znakov)
        self.current_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Preveri ujemanje s peer nodom — pošlji SAMO hash (ne celotnega besedila!)
        peer_hash = self._get_peer_hash()
        
        if peer_hash is None:
            print(f"[Slave {self.node_id}] Peer ni dosegljiv — zavržem besedilo.")
            self.current_text = None
            return False
        
        if self.current_hash == peer_hash:
            print(f"[Slave {self.node_id}] Hash se ujema ✓ — besedilo sprejeto.")
            return True
        else:
            print(f"[Slave {self.node_id}] Hash se NE ujema ✗ — besedilo zavrženo!")
            self.current_text = None
            self.current_hash = None
            return False

    def _get_peer_hash(self) -> str:
        """
        Pokliče peer slave node in zahteva njegov hash.
        Optimizacija: pošljemo SAMO hash (32 bajtov), ne celotnega besedila!
        """
        try:
            with grpc.insecure_channel(self.peer_address) as channel:
                # stub = sync_pb2_grpc.SlaveSyncStub(channel)
                # response = stub.CompareHash(sync_pb2.HashMessage(hash=self.current_hash))
                # return self.current_hash if response.match else "MISMATCH"
                pass  # Implementacija z dejanskim gRPC stubom
        except Exception as e:
            return None

# Optimizacija komunikacije med slave nodoma:
# - Slave 1 pošlje hash Slave 2 (64 bajtov)
# - Slave 2 primerja s svojim hashem in vrne bool (1 bajt)
# SKUPAJ: 65 bajtov namesto 2x polno besedilo!
