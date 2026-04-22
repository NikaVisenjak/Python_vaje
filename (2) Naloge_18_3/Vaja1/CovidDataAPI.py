import requests
import matplotlib.pyplot as plt
from datetime import date

response = requests.get('https://api.sledilnik.org/api/stats')

res = response.json()

# (a) Narisite dnevno stevilo pozitivnih slucajev.

pozitivni = []
datumi = []

for i in range(len(res) - 1):
    dan = res[i]

    datum = date(dan['year'], dan['month'], dan['day'])
    datumi.append(datum)

    #preverimo ali 'today' sploh obstaja
    if 'today' in dan['tests']['positive']:
        st_pozitivnih = dan['tests']['positive']['today']
    else:
        st_pozitivnih = 0

    pozitivni.append(st_pozitivnih)

#izris

plt.plot(datumi, pozitivni)
plt.show()

# (b) Narisite tedensko povprecje pozitivnih slucajev iz Maribora.

mb_pozitivni = [res[i]['statePerRegion']['mb'] for i in range(0, len(res) - 1)]

# zamenjamo None z 0
mb_pozitivni = [x if x is not None else 0 for x in mb_pozitivni]

weekly_avg = []

for i in range(0, len(mb_pozitivni), 7):
    teden = mb_pozitivni[i:i+7]
    
    povprecje = sum(teden) / len(teden)

    weekly_avg.append(povprecje)

plt.plot(weekly_avg)
plt.show()
