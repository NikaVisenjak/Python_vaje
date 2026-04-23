# =============================================================
# Izpit 2 - Naloga 2: gRPC igra z 2D koordinatami (Bayes)
# Server ima mizo z neznanimi dimenzijami in naključno točko.
# Klient ugiba koordinate, server vrne smer (S, SV, V, JV, J, JZ, Z, SZ)
# Klient mora zadeti z najmanjšim številom poskusov → bisekcija!
# =============================================================

# ---- game2d.proto ----
# syntax = "proto3";
#
# service BayesGame {
#   rpc StartGame (Empty) returns (GameInfo);
#   rpc Guess (GuessRequest) returns (GuessResponse);
# }
#
# message Empty {}
# message GameInfo { int32 width = 1; int32 height = 2; }  // dimenzije mize
# message GuessRequest { int32 x = 1; int32 y = 2; }
# message GuessResponse {
#   bool correct = 1;
#   string direction = 2;  // "S", "SV", "V", "JV", "J", "JZ", "Z", "SZ" ali "ZADETEK"
# }

# =============================================================
# SERVER
# =============================================================
import grpc
import random
from concurrent import futures
import game2d_pb2
import game2d_pb2_grpc

class BayesGameServicer(game2d_pb2_grpc.BayesGameServicer):
    def __init__(self):
        # Server si izmisli mizo in točko ob prvem klicu
        self.width = random.randint(10, 100)
        self.height = random.randint(10, 100)
        self.secret_x = random.randint(0, self.width)
        self.secret_y = random.randint(0, self.height)
        print(f"[Server] Miza: {self.width}x{self.height}, točka: ({self.secret_x}, {self.secret_y})")

    def StartGame(self, request, context):
        # Vrni dimenzije mize (ne točke!)
        return game2d_pb2.GameInfo(width=self.width, height=self.height)

    def Guess(self, request, context):
        gx, gy = request.x, request.y

        if gx == self.secret_x and gy == self.secret_y:
            return game2d_pb2.GuessResponse(correct=True, direction="ZADETEK")

        # Določi smer relativno na ugibanje → kje je PRAVA točka glede na ugibanje
        dx = self.secret_x - gx  # pozitivno = točka je VZHODNO od ugibanja
        dy = self.secret_y - gy  # pozitivno = točka je SEVERNO od ugibanja (y raste navzgor)

        if dx == 0:
            direction = "S" if dy > 0 else "J"
        elif dy == 0:
            direction = "V" if dx > 0 else "Z"
        elif dx > 0 and dy > 0:
            direction = "SV"
        elif dx > 0 and dy < 0:
            direction = "JV"
        elif dx < 0 and dy > 0:
            direction = "SZ"
        else:
            direction = "JZ"

        return game2d_pb2.GuessResponse(correct=False, direction=direction)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    game2d_pb2_grpc.add_BayesGameServicer_to_server(BayesGameServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server teče na portu 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()


# =============================================================
# CLIENT — z binarno/bisekcijsko strategijo (najmanj poskusov)
# =============================================================
import grpc
import game2d_pb2
import game2d_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = game2d_pb2_grpc.BayesGameStub(channel)

        # Pridobi dimenzije mize
        info = stub.StartGame(game2d_pb2.Empty())
        width, height = info.width, info.height
        print(f"[Client] Miza je {width}x{height}.")

        # Začetne meje za binarno iskanje po x in y oseh
        x_low, x_high = 0, width
        y_low, y_high = 0, height

        poskusi = 0

        while True:
            # Ugibaj sredino trenutnih mej (bisekcija)
            gx = (x_low + x_high) // 2
            gy = (y_low + y_high) // 2
            poskusi += 1

            response = stub.Guess(game2d_pb2.GuessRequest(x=gx, y=gy))
            print(f"[Client] Poskus {poskusi}: ({gx}, {gy}) → {response.direction}")

            if response.correct:
                print(f"[Client] Zadel v {poskusi} poskusih!")
                break

            d = response.direction

            # Prilagodi meje glede na smer (kje je prava točka)
            if "V" in d:
                x_low = gx + 1   # točka je vzhodno → dvigni spodnjo mejo x
            elif "Z" in d:
                x_high = gx - 1  # točka je zahodno → spusti zgornjo mejo x

            if "S" in d:
                y_low = gy + 1   # točka je severno → dvigni spodnjo mejo y
            elif "J" in d:
                y_high = gy - 1  # točka je južno → spusti zgornjo mejo y

if __name__ == '__main__':
    run()
