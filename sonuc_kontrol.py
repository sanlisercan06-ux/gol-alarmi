"""GECICI: canli IY 2,5 Ust oran okumasini gercek veride dener (Telegram yok). Kontrol sonrasi silinecek."""
import gol_alarmi as g

maclar = g.api_get("fixtures", live="all").get("response", [])
ilk = [m for m in maclar if m["fixture"]["status"]["short"] == "1H"]
print("canli:", len(maclar), "ilk yari:", len(ilk))
for m in ilk[:15]:
    ad = f"{m['teams']['home']['name']} - {m['teams']['away']['name']}"
    print("DENEME |", ad, "| dk", m["fixture"]["status"]["elapsed"], "| skor", m["goals"], "|", g.iy_orani(m["fixture"]["id"]))
