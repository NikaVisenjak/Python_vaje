# =============================================================
# Izpit 1 - Naloga 2: gRPC igra ugibanja števila
# Server naključno izbere število med a in b,
# klient ugiba. Točke se štejejo za oba.
# =============================================================

# ---- game.proto ----
# syntax = "proto3";
#
# service GuessGame {
#   rpc Play (GuessRequest) returns (GuessResponse);
# }
#
# message GuessRequest {
#   int32 a = 1;       // spodnja meja
#   int32 b = 2;       // zgornja meja
#   int32 guess = 3;   // ugibanje
# }
#
# message GuessResponse {
#   bool correct = 1;         // ali je ugibanje pravilno
#   int32 secret = 2;         // razkrije pravo število po igri
#   int32 player_score = 3;   // trenutne točke klienta
#   int32 server_score = 4;   // trenutne točke serverja
# }

# =============================================================
# SERVER
# =============================================================
# Zaženi: python server.py
# Potrebuješ: pip install grpcio grpcio-tools
# Generiraj kodo: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. game.proto

import grpc
import random
from concurrent import futures
import game_pb2
import game_pb2_grpc

class GuessGameServicer(game_pb2_grpc.GuessGameServicer):
    def __init__(self):
        # Inicializacija točk — ostanejo med sejami, ker je en objekt
        self.player_score = 0
        self.server_score = 0

    def Play(self, request, context):
        a = request.a
        b = request.b
        guess = request.guess

        # Server naključno izbere število v območju [a, b]
        secret = random.randint(a, b)

        if guess == secret:
            # Klient je zadel → dobi točko
            self.player_score += 1
            correct = True
        else:
            # Klient je zgrešil → server dobi točko
            self.server_score += 1
            correct = False

        # Vrni rezultat z vsemi informacijami
        return game_pb2.GuessResponse(
            correct=correct,
            secret=secret,
            player_score=self.player_score,
            server_score=self.server_score
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    game_pb2_grpc.add_GuessGameServicer_to_server(GuessGameServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server teče na portu 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()


# =============================================================
# CLIENT
# =============================================================
# Zaženi: python client.py

import grpc
import game_pb2
import game_pb2_grpc

def run():
    # Poveži se na server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = game_pb2_grpc.GuessGameStub(channel)

        print("Dobrodošel v igri ugibanja!")

        while True:
            try:
                # Klient vnese meje
                a = int(input("Vnesi spodnjo mejo (a): "))
                b = int(input("Vnesi zgornjo mejo (b): "))

                if a >= b:
                    print("a mora biti manjši od b!")
                    continue

                # Klient vnese ugibanje
                guess = int(input(f"Ugibaj število med {a} in {b}: "))

                # Pošlji zahtevo serverju
                response = stub.Play(game_pb2.GuessRequest(a=a, b=b, guess=guess))

                if response.correct:
                    print(f"✓ Pravilno! Število je bilo {response.secret}. Dobiš točko!")
                else:
                    print(f"✗ Narobe. Število je bilo {response.secret}. Server dobi točko.")

                print(f"Stanje točk → Ti: {response.player_score} | Server: {response.server_score}")
                print("-" * 40)

                nadaljevati = input("Igraj še enkrat? (da/ne): ")
                if nadaljevati.lower() != 'da':
                    break

            except ValueError:
                print("Napaka: vnesi veljavno celo število.")

if __name__ == '__main__':
    run()
