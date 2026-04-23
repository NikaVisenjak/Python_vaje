import re

# regex: beseda do 100 znakov (črke)
pattern = re.compile(r"^[a-zA-Z]{1,100}$")

def je_palindrom(beseda):
    # najprej preveri regex (validna beseda)
    if not pattern.match(beseda):
        return False

    # potem palindrom logika
    return beseda.lower() == beseda[::-1].lower()


# TESTI
testi = [
    "ana",
    "malayalam",
    "test",
    "Radar",
    "123",        # ne velja
    "a"
]

for t in testi:
    print(t, "->", je_palindrom(t))