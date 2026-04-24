import socket 

HOST = 'localhost'
PORT = 8888

def recv_exact(conn, n):
    data = b''
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Povezava prekinjena.")
        data += chunk
    return data

def decode_triplet(triple: bytes) -> int:
    #majority voting (3 bajti + 1 bajt)
    return max(set(triple), key=triple.count)

def decode(data: bytes) -> bytes:
    if len(data) % 3 != 0:
        raise ValueError("Neveljavna dolzina (ni deljivo s tri)")
    
    decoded = bytearray()

    for i in range(0, len(data), 3):
        triple = data[i: i+3]
        decoded.append(decode_triplet(triple))

    return bytes(decoded)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    print("Streznik poslusa...")

    while True:
        conn, addr = s.accept()
        with conn:
            print("Povezan: ", addr)

            try:
                # 1. header (10 B)
                header = recv_exact(conn, 10)
                length = int(header.decode().strip())

                # 2. vsebina
                encoded_data = recv_exact(conn, length)

                # 3. dekodiranje
                decoded_data = decode(encoded_data)

                print("Prejeto: ", decoded_data.decode('utf-8'))

            except Exception as e:
                print("Napaka: ", e)
    
