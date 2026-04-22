import socket
import threading
 
HOST, PORT = '127.0.0.1', 1234
 
users = {}
users_lock = threading.Lock()
 
def makeHeader(length: int) -> bytes:
    return str(length).encode('utf-8').ljust(10)
 
def receiveUser(sock):
    header = sock.recv(10)
    user = sock.recv(int(header)).decode('utf-8')
    return user
 
def receiveMessage(sock):
    header = sock.recv(10)
    data = sock.recv(int(header)).decode('utf-8')
    return data
 
def broadcast(sender_sock, sender_name, message):
    encoded_name = sender_name.encode('utf-8')
    encoded_msg = message.encode('utf-8')
    data = (
        makeHeader(len(encoded_name)) + encoded_name +
        makeHeader(len(encoded_msg)) + encoded_msg
    )
    with users_lock:
        for sock in list(users.keys()):
            if sock is not sender_sock:
                try:
                    sock.sendall(data)
                except:
                    pass
 
def handleClient(conn, addr):
    print(f"Connection established with {addr}.")
    try:
        uporabnik = receiveUser(conn)
        with users_lock:
            users[conn] = uporabnik
            print("Povezani uporabniki: {}".format(list(users.values())))
        print("{} se je pridruzil".format(uporabnik))
 
        while True:
            sporocilo = receiveMessage(conn)
            print("{}: {}".format(uporabnik, sporocilo))
            broadcast(conn, uporabnik, sporocilo)
 
    except:
        pass
    finally:
        with users_lock:
            users.pop(conn, None)
            print("Povezani uporabniki: {}".format(list(users.values())))
        conn.close()
        print(f"Connection with {addr} closed.")
 
def startServer():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("Streznik poslusa na {}:{}".format(HOST, PORT))
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handleClient, args=(conn, addr))
            thread.daemon = True
            thread.start()
            print(f"Active connections: {threading.active_count() - 1}")
 
if __name__ == "__main__":
    startServer()