# =============================================================
# Izpit 3 (september 2024) - Naloga 3: Regex bibliografija
# 4 različni pogoji iskanja
# =============================================================

import re

with open("bibliografija.txt", "r", encoding="utf-8") as f:
    vsebina = f.read()

# Razdeli na posamezne BibTeX vnose
vnosi = re.findall(r'@\w+\{[^@]+\}', vsebina, re.DOTALL)

# ----------------------------------------------------------
# 1. Vse članki, objavljeni v letu 2023
# ----------------------------------------------------------
vzorec_2023 = re.compile(r'year\s*=\s*\{?2023\}?', re.IGNORECASE)
clanki_2023 = [v for v in vnosi if vzorec_2023.search(v)]
print(f"=== Članki iz leta 2023 ({len(clanki_2023)}) ===")
for v in clanki_2023:
    print(v.strip())
    print("-" * 50)

# ----------------------------------------------------------
# 2. Vse članki s "machine learning" v naslovu
# ----------------------------------------------------------
vzorec_ml = re.compile(r'title\s*=\s*\{[^}]*machine learning[^}]*\}', re.IGNORECASE)
clanki_ml = [v for v in vnosi if vzorec_ml.search(v)]
print(f"\n=== Članki z 'machine learning' v naslovu ({len(clanki_ml)}) ===")
for v in clanki_ml:
    print(v.strip())
    print("-" * 50)

# ----------------------------------------------------------
# 3. Vse članki, kjer je PRVI avtor "John Smith"
# V BibTeX je author = "Priimek, Ime and Ime2 Priimek2 and ..."
# Iščemo: author = {John Smith and ...} ali {Smith, John and ...}
# ----------------------------------------------------------
vzorec_avtor = re.compile(
    r'author\s*=\s*\{(John Smith|Smith,\s*John)(\s+and\s+|\})',
    re.IGNORECASE
)
clanki_avtor = [v for v in vnosi if vzorec_avtor.search(v)]
print(f"\n=== Članki s prvim avtorjem 'John Smith' ({len(clanki_avtor)}) ===")
for v in clanki_avtor:
    print(v.strip())
    print("-" * 50)

# ----------------------------------------------------------
# 4. Vse članki z vsaj tremi avtorji
# Štejemo "and" v polju author — 2x "and" = 3 avtorji
# ----------------------------------------------------------
def stevilo_avtorjev(vnos):
    """Vrne število avtorjev iz polja author."""
    m = re.search(r'author\s*=\s*\{([^}]+)\}', vnos, re.IGNORECASE)
    if not m:
        return 0
    # Vsak "and" loči avtorje; število avtorjev = število "and" + 1
    avtor_string = m.group(1)
    return len(re.findall(r'\band\b', avtor_string, re.IGNORECASE)) + 1

clanki_3plus = [v for v in vnosi if stevilo_avtorjev(v) >= 3]
print(f"\n=== Članki z vsaj 3 avtorji ({len(clanki_3plus)}) ===")
for v in clanki_3plus:
    print(v.strip())
    print("-" * 50)
