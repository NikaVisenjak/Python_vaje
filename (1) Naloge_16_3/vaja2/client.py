import socket

def makeHeader(length: int) -> bytes:
    # Ustvari 10-bajtni header z dolžino vsebine.
    return str(length).encode().ljust(10)

def sendMessage(sock, content1: str, content2: str):
    # header1, vsebina1, header2, vsebina2
    data1 = content1.encode()
    data2 = content2.encode()

    message = (
        makeHeader(len(data1)) + data1 + makeHeader(len(data2)) + data2
    )
    sock.sendall(message)

def receiveMessage(sock):
    header = sock.recv(10)
    message = sock.recv(int(header)).decode()
    return message

def main():
    HOST, PORT = '127.0.0.1', 1235
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print("Client povezan na ", HOST, ":", PORT)

        vsebina1 = input("Napisi sporocilo 1: ")
        vsebina2 = input("Napisi sporocilo 2: ")

        sendMessage(client, vsebina1, vsebina2)
        print("Sporocilo je poslano.\n")

        odgovor1 = receiveMessage(client)
        odgovor2 = receiveMessage(client)

        if odgovor1 == odgovor2:
            print("Prejeto sporocilo: ", odgovor1)
        else:
            print("Prejeto sporocilo 1: ", odgovor1)
            print("Prejeto sporocilo 2: ", odgovor2)

if __name__ == "__main__":
    main()