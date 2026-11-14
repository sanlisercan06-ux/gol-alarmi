"""GECICI: bildirim giden maclarin ilk yari / mac sonu skorlarini yazar. Kontrol sonrasi silinecek."""
import json
import os
import urllib.parse
import urllib.request

MACLAR = [
    "Nyvelados - Dendele", "G3X - Desimpedidos Goti", "Funkbol - Loud", "Furia - Dibrados FC",
    "Santa Clara U23 - Torreense U23", "Colchester United U21 - Charlton Athletic U21", "Tavernes - Valencia",
    "Karaman FK - Talasgücü Belediyespor", "Finland U17 - Scotland U17", "Sunderland U21 - Paris Saint-Germain U21",
    "Smail - Bahla", "Paderborn II - Bochum II", "Cayman Islands - Guyana", "Real Potosí - Nacional Potosí",
    "TSV Hartberg - Floridsdorfer AC", "FC Helsingor - Holstebro",
]
GUNLER = ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14"]


def api(yol, **p):
    req = urllib.request.Request(f"https://v3.football.api-sports.io/{yol}?{urllib.parse.urlencode(p)}",
                                 headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


bulunan = {}
for g in GUNLER:
    for f in api("fixtures", date=g)["response"]:
        ad = f"{f['teams']['home']['name']} - {f['teams']['away']['name']}"
        if ad in MACLAR:
            bulunan.setdefault(ad, f)

for ad in MACLAR:
    f = bulunan.get(ad)
    if not f:
        print(f"YOK | {ad}")
        continue
    s = f["score"]
    print(f"{f['fixture']['status']['short']} | {ad} | {f['league']['name']} ({f['league']['country']}) | "
          f"IY {s['halftime']['home']}-{s['halftime']['away']} | MS {s['fulltime']['home']}-{s['fulltime']['away']} | "
          f"sure {f['fixture']['status']['elapsed']}")
