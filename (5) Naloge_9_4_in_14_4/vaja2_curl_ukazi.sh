# ================================================================
# VAJE 9.4 - Vaja 2: InfluxDB preko CURL
# InfluxDB server: 127.0.0.1:1234
# Uporabnik: guest, Geslo: guest
# ================================================================
# OPOMBA: Vse curl ukaze izvajaj v terminalu (Linux/Mac/WSL).
# Na začetek vsakega ukaza dodamo: curl -u uporabnik:geslo -> guest:guest
# ================================================================

# ----------------------------------------------------------------
# (a) Ustvari svoj novi database
# ----------------------------------------------------------------
# Pošljemo POST zahtevo na /query endpoint z InfluxQL ukazom
# CREATE DATABASE ustvari novo bazo s tvojim imenom

curl -u uporabnik:geslo -X POST \
  "http://127.0.0.1:1234/query" \
  --data-urlencode "q=CREATE DATABASE mojDatabase"

# Preveri, da je bila ustvarjena (izpiše seznam vseh databaz):
curl -u uporabnik:geslo \
  "http://127.0.0.1:1234/query?q=SHOW+DATABASES"


# ----------------------------------------------------------------
# (b) Direktno vpiši eno točko v database
# ----------------------------------------------------------------
# InfluxDB Line Protocol format:
#   <measurement>,<tag_key>=<tag_value> <field_key>=<field_value> [timestamp]
#
# "Temperature" = ime meritve (measurement)
# T1=-0.14     = ime polja (field) in vrednost
# Timestamp je neobvezen — če ga izpustimo, InfluxDB doda trenutni čas

curl -u uporabnik:geslo -X POST \
  "http://127.0.0.1:1234/write?db=mojDatabase" \
  --data-binary "Temperature T1=-0.14"

# Preverimo, da je bila točka zapisana:
curl -u uporabnik:geslo \
  "http://127.0.0.1:1234/query?db=mojDatabase" \
  --data-urlencode "q=SELECT * FROM Temperature"


# ----------------------------------------------------------------
# (c) Vpiši točke iz datoteke
# ----------------------------------------------------------------
# Najprej ustvari datoteko data.txt z več točkami v Line Protocol formatu.
# Vsaka vrstica = ena točka meritve.
# Format: measurement,tag=vrednost field=vrednost timestamp_v_nanosekundah

# Primer vsebine datoteke data.txt:
# Temperature,user=student T1=21.5,T2=22.1 1700000000000000000
# Temperature,user=student T1=21.8,T2=22.3 1700000001000000000
# Pressure,user=student P1=1013.2,P2=1012.8 1700000000000000000
# Pressure,user=student P1=1013.5,P2=1012.9 1700000001000000000

# Napiši datoteko (v bash):
cat > data.txt << 'EOF'
Temperature,user=student T1=21.5,T2=22.1 1700000000000000000
Temperature,user=student T1=21.8,T2=22.3 1700000001000000000
Temperature,user=student T1=20.9,T2=21.7 1700000002000000000
Pressure,user=student P1=1013.2,P2=1012.8 1700000000000000000
Pressure,user=student P1=1013.5,P2=1012.9 1700000001000000000
Pressure,user=student P1=1013.1,P2=1012.6 1700000002000000000
EOF

# Pošlji celotno datoteko z --data-binary @ime_datoteke
# @ pomeni "preberi vsebino iz datoteke"
curl -u uporabnik:geslo -X POST \
  "http://127.0.0.1:1234/write?db=mojDatabase" \
  --data-binary @data.txt


# ----------------------------------------------------------------
# (d) Zahtevaj podatke nazaj in shrani v datoteko
# ----------------------------------------------------------------
# Poizvedba vrne JSON z vsemi točkami iz meritve Temperature
# Rezultat preusmerimo v datoteko z > rezultat.json

curl -u uporabnik:geslo \
  "http://127.0.0.1:1234/query?db=mojDatabase&pretty=true" \
  --data-urlencode "q=SELECT * FROM Temperature" \
  > rezultat_temperature.json

# Enako za Pressure:
curl -u uporabnik:geslo \
  "http://127.0.0.1:1234/query?db=mojDatabase&pretty=true" \
  --data-urlencode "q=SELECT * FROM Pressure" \
  > rezultat_pressure.json

# Preveri vsebino datoteke:
cat rezultat_temperature.json
