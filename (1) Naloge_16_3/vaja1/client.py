import socket

def ClientProgram():
    HOST = '127.0.0.1'
    PORT = 1234

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        client.sendall("Zivijo!".encode('utf-8'))
        data = client.recv(1024)
        if data:
            print("Streznik odgovarja: " + data.decode('utf-8'))


if __name__ == "__main__":
    ClientProgram()