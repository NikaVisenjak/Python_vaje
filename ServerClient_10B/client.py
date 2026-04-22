import socket 

HOST = 'localhost'
PORT = 8888

def encode(data: bytes) -> bytes:
    #vsak bajt 3x
    encoded = bytearray()
    for b in data:
        encoded.extend([b, b, b])
    return bytes(encoded)

def sendMessage(msg: str):
    raw = msg.encode('utf-8')
    encoded = encode(raw)

    #header
    header = f"{len(encoded):<10}".encode('utf-8')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(header + encoded)

    print("sporocilo poslano.")


if __name__ == '__main__':
    sendMessage("Hello world!")
