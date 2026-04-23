# =============================================================
# Izpit 2 - Naloga 3: Regex nad bibliografijo
# Preberi datoteko in izpiši vnose z letnico 2002-2015,
# ki so objavljeni pri "American Physical Society"
# =============================================================

import re

# Preberi celotno datoteko v en string
with open("bibliografija.txt", "r", encoding="utf-8") as f:
    vsebina = f.read()

# Razdeli na posamezne BibTeX vnose (od @ do naslednjega @)
vnosi = re.findall(r'@\w+\{[^@]+\}', vsebina, re.DOTALL)

# Regex za letnico 2002-2015
vzorec_letnice = re.compile(r'year\s*=\s*\{?(200[2-9]|201[0-5])\}?', re.IGNORECASE)

# Regex za založbo "American Physical Society"
# Iščemo v polju publisher = {...American Physical Society...}
vzorec_aps = re.compile(r'publisher\s*=\s*\{[^}]*American Physical Society[^}]*\}', re.IGNORECASE)

# Filtriraj: oba pogoja morata biti izpolnjena
ujemajoci = [
    vnos for vnos in vnosi
    if vzorec_letnice.search(vnos) and vzorec_aps.search(vnos)
]

print(f"Najdenih {len(ujemajoci)} vnosov (2002-2015, APS):\n")
for vnos in ujemajoci:
    print(vnos.strip())
    print("-" * 60)
