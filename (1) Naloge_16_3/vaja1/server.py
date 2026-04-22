import socket

def ServerProgram():
    HOST = '127.0.0.1'
    PORT = 1234

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))

    server.listen(1)

    conn, addr = server.accept()
    print("Connection from: " + str(addr))

    with conn:
       data = conn.recv(1024) 
       if data:
           text = data.decode("utf-8")
           print("Client sporoca: " + text)
           conn.sendall(text.upper().encode('utf-8'))
    server.close()


if __name__ == "__main__":
    ServerProgram()