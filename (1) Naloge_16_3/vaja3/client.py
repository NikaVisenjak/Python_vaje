import socket
import threading

HOST, PORT = '127.0.0.1', 1234

def makeHeader(length: int) -> bytes:
    return str(length).encode('utf-8').ljust(10)

def sendUsername(sock, username: str):
    encoded = username.encode('utf-8')
    sock.sendall(makeHeader(len(encoded)) + encoded)

def sendMessages(sock):
    while True:
        text = input()
        encoded = text.encode('utf-8')
        sock.sendall(makeHeader(len(encoded)) + encoded)

def receiveMessages(sock):
    while True:
        try:
            header_ime = sock.recv(10)
            username = sock.recv(int(header_ime)).decode('utf-8')
            header_sporocilo = sock.recv(10)
            message = sock.recv(int(header_sporocilo)).decode('utf-8')
            print(f"{username}: {message}")
        except:
            print("Povezava prekinjena.")
            break

def connectToChat():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("Uspesno povezan na: {}:{}".format(HOST, PORT))

        username = input("Vpisi svoje uporabnisko ime: ")
        sendUsername(s, username)

        # ločen thread za prejemanje
        recv_thread = threading.Thread(target=receiveMessages, args=(s,))
        recv_thread.daemon = True
        recv_thread.start()

        # glavni thread pošilja
        sendMessages(s)

if __name__ == "__main__":
    connectToChat()