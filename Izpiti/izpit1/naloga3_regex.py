# =============================================================
# Izpit 1 - Naloga 3: Regex nad bibliografijo
# Preberi datoteko "bibliografija.txt" in izpiši vse vnose
# z letnico 2002-2015 (vključno).
# =============================================================

import re

# Preberi celotno datoteko v en string
with open("bibliografija.txt", "r", encoding="utf-8") as f:
    vsebina = f.read()

# Razdeli vsebino na posamezne BibTeX vnose.
# Vsak vnos začne z "@" in konča z "}" na začetku vrstice.
# Vzorec ujame vse od "@Tip{kljuc," do zaključnega "}"
vnosi = re.findall(r'@\w+\{[^@]+\}', vsebina, re.DOTALL)

# Regex vzorec za letnico med 2002 in 2015 (vključno):
# Iščemo polje "year = {XXXX}" ali "year = XXXX"
# Letnice: 200[2-9] ali 201[0-5]
vzorec_letnice = re.compile(r'year\s*=\s*\{?(200[2-9]|201[0-5])\}?', re.IGNORECASE)

# Filtriraj vnose, ki ustrezajo zahtevani letnici
ujemajoci = [vnos for vnos in vnosi if vzorec_letnice.search(vnos)]

# Izpiši rezultate
print(f"Najdenih {len(ujemajoci)} vnosov z letnico 2002-2015:\n")
for vnos in ujemajoci:
    print(vnos.strip())
    print("-" * 60)
