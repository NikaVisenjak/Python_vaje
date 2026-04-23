import re

# mapa mesecev (BibTeX format → številka)
month_map = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

# preberi datoteko
with open("bibliografija.txt", "r", encoding="utf-8") as f:
    text = f.read()

entries = re.findall(r'@\w+\{[^@]*?\n\}', text, re.DOTALL)

def get_sort_key(entry):
    # leto
    year_match = re.search(r'year\s*=\s*\{(\d{4})\}', entry)
    year = int(year_match.group(1)) if year_match else 0

    # mesec
    # najdi month = {NEKA_BESEDA} in mi vrni samo besedo
    month_match = re.search(r'month\s*=\s*\{(\w+)\}', entry)
    month_str = month_match.group(1).lower() if month_match else "jan"

    month = month_map.get(month_str, 0)

    # ključ
    key_match = re.search(r'@\w+\{([^,]+)', entry)
    key = key_match.group(1) if key_match else ""

    return (year, month, key)

# sortiranje
sorted_entries = sorted(entries, key=get_sort_key)

# zapis v novo datoteko
with open("sorted.txt", "w", encoding="utf-8") as f:
    for entry in sorted_entries:
        f.write(entry.strip() + "\n\n")