import re

# Preberemo datoteko
with open("3_bibliografija.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Razdelimo vsebino na posamezne BibTeX vnose.
# re.split() razdeli niz na podlagi vzorca.
# Vzorec: r'\n(?=@)'
#   \n        - ujame znak za novo vrstico
#   (?=@)     - pozitivni lookahead: razdeli SAMO tam, kjer za \n sledi znak @
#               (lookahead ne "porabi" znaka @, zato @ ostane v naslednjem delu)
# Rezultat: seznam nizov, vsak začne z "@Article{...}" ali podobno
entries = re.split(r'\n(?=@)', content)


def get_field(entry, field):
    # Poišče vrednost določenega polja (npr. title, author, year) v BibTeX vnosu.
    # re.search() poišče PRVI ujemajoči se vzorec kjerkoli v nizu.
    # Vzorec (rf-string, ker vstavimo spremenljivko {field}):
    #   {field}   - ime polja, npr. "title" ali "author"
    #   \s*       - nič ali več presledkov/tabulatorjev
    #   =         - znak enačaja (BibTeX sintaksa: title = {...})
    #   \s*       - nič ali več presledkov za enačajem
    #   \{{       - dobesedna { (escaped, ker {} pomeni posebno stvar v f-stringu)
    #   (.+?)     - capture group: ujame enega ali več znakov, ? = "lazy" (čim manj)
    #               brez ? bi ujel vse do ZADNJE }, z ? se ustavi pri PRVI }
    #   \}}       - dobesedna }
    # Zastavici:
    #   re.IGNORECASE - ne razlikuje med velikimi/malimi črkami (Title == title)
    #   re.DOTALL     - pika (.) ujame tudi znak \n (za večvrstična polja)
    match = re.search(rf'{field}\s*=\s*\{{(.+?)\}}', entry, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def get_authors(entry):
    authors_raw = get_field(entry, "author")
    if not authors_raw:
        return []
    # Razdeli niz avtorjev na seznam posameznih avtorjev.
    # V BibTeX-u so avtorji ločeni z besedo "and", npr.:
    #   "Janez Novak and Ana Kovač and Peter Kos"
    # re.split() razdeli niz na podlagi vzorca:
    #   \s+   - en ali več presledkov pred "and"
    #   and   - dobesedna beseda "and"
    #   \s+   - en ali več presledkov za "and"
    # Zastavica re.IGNORECASE ujame tudi "AND" ali "And"
    return [a.strip() for a in re.split(r'\s+and\s+', authors_raw, flags=re.IGNORECASE)]


# 1. Članki iz leta 2014
print("=" * 60)
print("1. ČLANKI IZ LETA 2014:")
print("=" * 60)
found = False
for entry in entries:
    # re.search() poišče vzorec kjerkoli v nizu entry.
    # Vzorec: r'year\s*=\s*\{2014\}'
    #   year    - dobesedna beseda "year"
    #   \s*     - nič ali več presledkov
    #   =       - znak enačaja
    #   \s*     - nič ali več presledkov
    #   \{2014\} - dobesedna {2014} (oklepaji so escaped z \)
    # Zastavica re.IGNORECASE ujame tudi "Year = {2014}"
    if re.search(r'year\s*=\s*\{2014\}', entry, re.IGNORECASE):
        title = get_field(entry, "title")
        author = get_field(entry, "author")
        print(f"  Naslov: {title}\n  Avtor(ji): {author}\n")
        found = True
if not found:
    print("  Ni najdenih člankov iz leta 2014.\n")

# 2. Članki z "measuring Information" v naslovu
print("=" * 60)
print("2. ČLANKI Z 'measuring Information' V NASLOVU:")
print("=" * 60)
found = False
for entry in entries:
    title = get_field(entry, "title")
    # re.search() poišče vzorec kjerkoli v spremenljivki title.
    # Vzorec: r'measuring Information'
    #   measuring   - dobesedna beseda "measuring"
    #   (presledek) - dobesedni presledek med besedama
    #   Information - dobesedna beseda "Information"
    # Zastavica re.IGNORECASE poskrbi, da ujame tudi
    #   "Measuring information", "MEASURING INFORMATION" itd.
    if re.search(r'measuring Information', title, re.IGNORECASE):
        author = get_field(entry, "author")
        year = get_field(entry, "year")
        print(f"  Naslov: {title}\n  Avtor(ji): {author}\n  Leto: {year}\n")
        found = True
if not found:
    print("  Ni najdenih člankov z besedo 'measuring Information' v naslovu.\n")

# 3. Članki, kjer je prvi avtor "Milan Palu"
print("=" * 60)
print("3. ČLANKI S PRVIM AVTORJEM 'Milan Palu':")
print("=" * 60)
found = False
for entry in entries:
    authors = get_authors(entry)
    # Preverimo le prvega avtorja (authors[0]).
    # re.search() poišče vzorec kjerkoli v imenu prvega avtorja.
    # Vzorec: r'Milan\s+Palu'
    #   Milan   - dobesedno ime
    #   \s+     - en ali več presledkov (ujame tudi dvojni presledek)
    #   Palu    - začetek priimka (ne zahtevamo celotnega priimka,
    #             ker ima LaTeX posebne znake: Palu{\v{s}} = Paluš)
    #             Tako ujamemo "Paluš", "Palus", "Palu..." ne glede na kodiranje
    # Zastavica re.IGNORECASE ujame tudi "milan palu"
    if authors and re.search(r'Milan\s+Palu', authors[0], re.IGNORECASE):
        title = get_field(entry, "title")
        year = get_field(entry, "year")
        print(f"  Naslov: {title}\n  Avtor(ji): {get_field(entry, 'author')}\n  Leto: {year}\n")
        found = True
if not found:
    print("  Ni najdenih člankov s prvim avtorjem 'Milan Palu'.\n")

# 4. Članki z vsaj tremi avtorji
print("=" * 60)
print("4. ČLANKI Z VSAJ TREMI AVTORJI:")
print("=" * 60)
found = False
for entry in entries:
    # re.match() preverja vzorec SAMO na začetku niza (za razliko od re.search).
    # Vzorec: r'@(Article|InCollection|Book|Misc)'
    #   @           - dobesedni znak @, s katerim začne vsak BibTeX vnos
    #   (           - začetek capture group
    #   Article     - tip vnosa za članke
    #   |           - ALI operator
    #   InCollection - tip vnosa za poglavja v knjigah
    #   |           - ALI operator
    #   Book        - tip vnosa za knjige
    #   |           - ALI operator
    #   Misc        - tip vnosa za ostalo
    #   )           - konec capture group
    # Namen: preskočimo komentarje (@Comment) in preambulo (@Preamble)
    # Zastavica re.IGNORECASE ujame tudi "@article", "@ARTICLE" itd.
    if not re.match(r'@(Article|InCollection|Book|Misc)', entry, re.IGNORECASE):
        continue
    authors = get_authors(entry)
    if len(authors) >= 3:
        title = get_field(entry, "title")
        year = get_field(entry, "year")
        print(f"  Naslov: {title}")
        print(f"  Število avtorjev: {len(authors)}")
        for i, a in enumerate(authors, 1):
            print(f"    {i}. {a}")
        print(f"  Leto: {year}\n")
        found = True
if not found:
    print("  Ni najdenih člankov z vsaj tremi avtorji.\n")