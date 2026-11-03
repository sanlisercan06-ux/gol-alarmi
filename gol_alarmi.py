"""
Gol Alarmi - Ilk 20 dakikada 2+ gol olan maclari Telegram'a bildirir.

Veri: ESPN acik skor servisi (anahtar gerekmez, tum ligler tek istekte).
Calisma: LOOP_MINUTES boyunca her POLL_SECONDS saniyede bir kontrol eder.
Ayni mac icin bir kez bildirim gonderir (sent.json'da saklanir).

Ortam degiskenleri:
  TELEGRAM_BOT_TOKEN  (zorunlu)
  TELEGRAM_CHAT_ID    (zorunlu)
  LOOP_MINUTES        (varsayilan 340 = ~5 saat 40 dk; 0 = tek tur)
  POLL_SECONDS        (varsayilan 60)
  GOL_ESIGI           (varsayilan 2)
  DAKIKA_SINIRI       (varsayilan 20)
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
LEAGUES_URL = "https://site.api.espn.com/apis/site/v2/leagues/dropdown?sport=soccer&limit=1000"
SENT_FILE =os.path.join(os.path.dirname(os.path.abspath(__file__)), "sent.json")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LOOP_MINUTES = int(os.environ.get("LOOP_MINUTES", "340"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))
GOL_ESIGI = int(os.environ.get("GOL_ESIGI", "2"))
DAKIKA_SINIRI = int(os.environ.get("DAKIKA_SINIRI", "20"))


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "gol-alarmi/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def telegram_gonder(metin):
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": metin,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=20) as r:
        return json.loads(r.read().decode("utf-8")).get("ok", False)


def sent_yukle():
    try:
        with open(SENT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def sent_kaydet(sent):
    # 3 gunden eski kayitlari at
    sinir = time.time() - 3 * 86400
    sent = {k: v for k, v in sent.items() if v > sinir}
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(sent, f)
    return sent


def gol_dakikasi(detay):
    """ "16'" -> 16, "45'+2'" -> 45. Okunamazsa clock.value'dan hesapla."""
    clock = detay.get("clock", {})
    m = re.match(r"(\d+)", clock.get("displayValue", ""))
    if m:
        return int(m.group(1))
    return int(clock.get("value", 99999) // 60) + 1


LIGLER = {}  # ESPN lig id -> lig adi


def ligleri_yukle():
    try:
        data = http_get_json(LEAGUES_URL)
        LIGLER.update({l["id"]: l["name"] for l in data.get("leagues", [])})
        log(f"{len(LIGLER)} lig yuklendi")
    except Exception as e:
        log(f"Lig listesi alinamadi: {e}")


def lig_adi(event):
    m = re.search(r"~l:(\d+)", event.get("uid", ""))
    if m and m.group(1) in LIGLER:
        return LIGLER[m.group(1)]
    slug = event.get("season", {}).get("slug", "")
    # "2026-27-english-premier-league" -> "English Premier League"
    slug = re.sub(r"^\d{4}(-\d{2,4})?-", "", slug)
    return slug.replace("-", " ").title() or "Bilinmeyen lig"


def erken_goller(event):
    comp = event["competitions"][0]
    takimlar = {c["team"]["id"]: c["team"]["displayName"] for c in comp["competitors"]}
    goller = []
    for d in comp.get("details", []):
        if not d.get("scoringPlay") or d.get("shootout"):
            continue
        dk = gol_dakikasi(d)
        if dk <= DAKIKA_SINIRI:
            takim = takimlar.get(d.get("team", {}).get("id"), "?")
            if d.get("ownGoal"):
                takim += " (kk)"
            goller.append((dk, takim))
    return sorted(goller)


def mesaj_olustur(event, goller):
    comp = event["competitions"][0]
    ev = next(c for c in comp["competitors"] if c["homeAway"] == "home")
    dep = next(c for c in comp["competitors"] if c["homeAway"] == "away")
    dakika = event["status"].get("displayClock", "")
    gol_satiri = ", ".join(f"{dk}' {t}" for dk, t in goller)
    link = next((l["href"] for l in event.get("links", []) if "summary" in l.get("rel", [])), "")
    return (
        f"⚽ İLK {DAKIKA_SINIRI} DK'DA {len(goller)} GOL!\n"
        f"🏆 {lig_adi(event)}\n"
        f"{ev['team']['displayName']} {ev['score']} - {dep['score']} {dep['team']['displayName']}\n"
        f"🥅 {gol_satiri}\n"
        f"⏱ Şu an: {dakika}\n"
        f"{link}"
    ).strip()


def tur(sent):
    data = http_get_json(ESPN_URL)
    canli = 0
    for event in data.get("events", []):
        if event.get("status", {}).get("type", {}).get("state") != "in":
            continue
        canli += 1
        eid = event["id"]
        if eid in sent:
            continue
        goller = erken_goller(event)
        if len(goller) >= GOL_ESIGI:
            metin = mesaj_olustur(event, goller)
            if telegram_gonder(metin):
                sent[eid] = time.time()
                sent = sent_kaydet(sent)
                log(f"BİLDİRİM: {event['name']}")
            else:
                log(f"Telegram hatasi: {event['name']}")
    log(f"{canli} canli mac tarandi")
    return sent


def main():
    if not TOKEN or not CHAT_ID:
        sys.exit("TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID gerekli")
    if os.environ.get("TEST_MESAJI") == "true":
        ok = telegram_gonder("✅ Gol Alarmı çalışıyor (test mesajı)")
        log(f"Test mesaji: {'gonderildi' if ok else 'HATA'}")
    sent = sent_yukle()
    ligleri_yukle()
    bitis = time.time() + LOOP_MINUTES * 60
    while True:
        try:
            sent = tur(sent)
        except Exception as e:  # ag hatasi vs. -> bir sonraki turda tekrar dene
            log(f"Hata: {e}")
        if time.time() + POLL_SECONDS >= bitis:
            break
        time.sleep(POLL_SECONDS)
    sent_kaydet(sent)


if __name__ == "__main__":
    main()
