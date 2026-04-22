import socket

def makeHeader(length: int) -> bytes:
    return str(length).encode().ljust(10)

def sendMessage(sock, msg1, msg2):
    if len(msg1) > len(msg2):
        data1 = msg1.encode()
        data2 = msg1.encode()
    elif len(msg1) == len(msg2):
        data1 = msg1.encode()
        data2 = msg2.encode()
    else:
        data1 = msg2.encode()
        data2 = msg2.encode()
    
    sock.sendall(makeHeader(len(data1)) + data1 + makeHeader(len(data2)) + data2)

def receiveMessage(sock):
    header = sock.recv(10)
    message = sock.recv(int(header)).decode()
    return message

def main():
    HOST, PORT = '127.0.0.1', 1235

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        conn, addr = server.accept()
        print("Povezan client: ", addr)

        message1 = receiveMessage(conn)
        message2 = receiveMessage(conn)

        print(f"Vsebina 1: {message1}")
        print(f"Vsebina 2: {message2}")

        sendMessage(conn, message1, message2)

        conn.close()

if __name__ == "__main__":
    main()