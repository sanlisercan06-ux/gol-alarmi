"""GECICI: canli oran pazar adlarini listeler. Kontrol sonrasi silinecek."""
import collections
import json
import os
import urllib.request

req = urllib.request.Request("https://v3.football.api-sports.io/odds/live",
                             headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]})
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.loads(r.read().decode("utf-8"))
print("errors:", d.get("errors"), "mac:", len(d.get("response", [])))
adlar = collections.Counter()
ornek = {}
for m in d.get("response", []):
    for b in m.get("odds", []):
        adlar[(b.get("id"), b.get("name"))] += 1
        if "half" in (b.get("name") or "").lower() and (b["id"], b["name"]) not in ornek:
            ornek[(b["id"], b["name"])] = (m["fixture"], m.get("status"), b.get("values")[:6])
for (i, n), c in adlar.most_common():
    print(f"PAZAR | {i} | {n} | {c}")
for k, v in ornek.items():
    print("ORNEK |", k, "|", json.dumps(v, ensure_ascii=False)[:600])
print("ILK MAC ANAHTARLARI |", list(d["response"][0].keys()) if d.get("response") else "-")
