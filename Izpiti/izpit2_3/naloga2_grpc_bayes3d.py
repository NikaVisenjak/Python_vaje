# =============================================================
# Izpit 3 (september 2024) - Naloga 2: gRPC igra z 3D sferično smer
# Server ima sfero z neznano velikostjo in naključno točko v 3D.
# Klient ugiba (x, y, z), server vrne smer (npr. "SV-zgoraj")
# Klient bisekcija po vseh 3 oseh → najmanj poskusov
# =============================================================

# ---- game3d.proto ----
# syntax = "proto3";
#
# service BayesGame3D {
#   rpc StartGame (Empty) returns (GameInfo3D);
#   rpc Guess (GuessRequest3D) returns (GuessResponse3D);
# }
#
# message Empty {}
# message GameInfo3D { int32 size = 1; }
# message GuessRequest3D { int32 x = 1; int32 y = 2; int32 z = 3; }
# message GuessResponse3D {
#   bool correct = 1;
#   string direction = 2;
# }

import grpc
import random
from concurrent import futures
import game3d_pb2
import game3d_pb2_grpc

# =============================================================
# SERVER
# =============================================================
class BayesGame3DServicer(game3d_pb2_grpc.BayesGame3DServicer):
    def __init__(self):
        # Sfera z naključno velikostjo
        self.size = random.randint(10, 100)
        # Naključna točka znotraj sfere (poenostavimo na kocko)
        self.sx = random.randint(0, self.size)
        self.sy = random.randint(0, self.size)
        self.sz = random.randint(0, self.size)
        print(f"[Server] Velikost: {self.size}, točka: ({self.sx}, {self.sy}, {self.sz})")

    def StartGame(self, request, context):
        return game3d_pb2.GameInfo3D(size=self.size)

    def Guess(self, request, context):
        gx, gy, gz = request.x, request.y, request.z

        if gx == self.sx and gy == self.sy and gz == self.sz:
            return game3d_pb2.GuessResponse3D(correct=True, direction="ZADETEK")

        # Smer po x/y osi (horizontalno)
        dx = self.sx - gx
        dy = self.sy - gy
        dz = self.sz - gz

        # Horizontalna komponenta (S/J/V/Z kombinacije)
        if dx == 0 and dy == 0:
            horiz = ""
        elif dx == 0:
            horiz = "S" if dy > 0 else "J"
        elif dy == 0:
            horiz = "V" if dx > 0 else "Z"
        elif dx > 0 and dy > 0:
            horiz = "SV"
        elif dx > 0 and dy < 0:
            horiz = "JV"
        elif dx < 0 and dy > 0:
            horiz = "SZ"
        else:
            horiz = "JZ"

        # Vertikalna komponenta
        if dz > 0:
            vert = "zgoraj"
        elif dz < 0:
            vert = "spodaj"
        else:
            vert = ""

        # Sestavi smer
        if horiz and vert:
            direction = f"{horiz}-{vert}"
        elif horiz:
            direction = horiz
        else:
            direction = vert

        return game3d_pb2.GuessResponse3D(correct=False, direction=direction)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    game3d_pb2_grpc.add_BayesGame3DServicer_to_server(BayesGame3DServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server teče na portu 50051...")
    server.wait_for_termination()


# =============================================================
# CLIENT — bisekcija po vseh 3 oseh
# =============================================================
def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = game3d_pb2_grpc.BayesGame3DStub(channel)

        info = stub.StartGame(game3d_pb2.Empty())
        size = info.size
        print(f"[Client] Sfera velikosti {size}.")

        # Začetne meje za vse 3 osi
        x_low, x_high = 0, size
        y_low, y_high = 0, size
        z_low, z_high = 0, size

        poskusi = 0

        while True:
            # Ugibaj sredino po vseh 3 oseh (3D bisekcija)
            gx = (x_low + x_high) // 2
            gy = (y_low + y_high) // 2
            gz = (z_low + z_high) // 2
            poskusi += 1

            response = stub.Guess(game3d_pb2.GuessRequest3D(x=gx, y=gy, z=gz))
            print(f"[Client] Poskus {poskusi}: ({gx}, {gy}, {gz}) → {response.direction}")

            if response.correct:
                print(f"[Client] Zadel v {poskusi} poskusih!")
                break

            d = response.direction

            # Prilagodi x meje
            if "V" in d:
                x_low = gx + 1
            elif "Z" in d:
                x_high = gx - 1

            # Prilagodi y meje
            if "S" in d:
                y_low = gy + 1
            elif "J" in d:
                y_high = gy - 1

            # Prilagodi z meje
            if "zgoraj" in d:
                z_low = gz + 1
            elif "spodaj" in d:
                z_high = gz - 1

if __name__ == '__main__':
    run()
