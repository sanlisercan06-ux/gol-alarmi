"""
Gol Alarmi - Ilk 20 dakikada 2+ gol olan maclari Telegram'a bildirir.

Veri: API-Football canli maclar (fixtures?live=all, tek istekte tum ligler).
Calisma: LOOP_MINUTES boyunca her POLL_SECONDS saniyede bir kontrol eder.
Ayni mac icin bir kez bildirim gonderir (sent.json'da saklanir).

Ortam degiskenleri:
  API_FOOTBALL_KEY    (zorunlu)
  TELEGRAM_BOT_TOKEN  (zorunlu)
  TELEGRAM_CHAT_ID    (zorunlu)
  LOOP_MINUTES        (varsayilan 340 = ~5 saat 40 dk; 0 = tek tur)
  POLL_SECONDS        (varsayilan 60)
  GOL_ESIGI           (varsayilan 2)
  DAKIKA_SINIRI       (varsayilan 20)
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

API_URL = "https://v3.football.api-sports.io/"
SENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sent.json")

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LOOP_MINUTES = int(os.environ.get("LOOP_MINUTES", "340"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))
GOL_ESIGI = int(os.environ.get("GOL_ESIGI", "2"))
DAKIKA_SINIRI = int(os.environ.get("DAKIKA_SINIRI", "20"))
UYARI_TUR = 30  # bu kadar tur ust uste hata olursa Telegram'a haber ver


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def api_get(yol, **param):
    url = API_URL + yol
    if param:
        url += "?" + urllib.parse.urlencode(param)
    req = urllib.request.Request(url, headers={"x-apisports-key": API_KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    # Kota veya plan sorununda bos liste de gelir, "mac yok" sanilmasin
    if data.get("errors"):
        raise RuntimeError(f"API hatasi: {data['errors']}")
    return data


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


def erken_goller(mac):
    goller = []
    for e in mac.get("events") or []:
        if e.get("type") != "Goal" or e.get("detail") == "Missed Penalty":
            continue
        dk = (e.get("time") or {}).get("elapsed")
        if dk is None or dk > DAKIKA_SINIRI:
            continue
        takim = (e.get("team") or {}).get("name") or "?"
        if e.get("detail") == "Own Goal":
            takim += " (kk)"
        goller.append((dk, takim))
    return sorted(goller)


def toplam_skor(mac):
    g = mac.get("goals") or {}
    return (g.get("home") or 0) + (g.get("away") or 0)


def skorla_erken_mi(mac):
    """Gol kaydi gecikse de ilk yarida saat 1-20 ve skor yeterliyse kural saglanmistir."""
    durum = mac["fixture"]["status"]
    dk = durum.get("elapsed")
    return durum.get("short") == "1H" and dk is not None and 1 <= dk <= DAKIKA_SINIRI and toplam_skor(mac) >= GOL_ESIGI


def mesaj_olustur(mac, goller):
    t, g, durum, lig = mac["teams"], mac["goals"], mac["fixture"]["status"], mac["league"]
    gol_sayisi = max(len(goller), GOL_ESIGI)
    gol_satiri = ", ".join(f"{dk}' {t2}" for dk, t2 in goller) or "Gol dakikaları henüz gelmedi (skor ve maç saatine göre)"
    ulke = f"{lig['country']}, " if lig.get("country") else ""
    return (
        f"⚽ İLK {DAKIKA_SINIRI} DK'DA {gol_sayisi} GOL!\n"
        f"🏆 {ulke}{lig.get('name', 'Bilinmeyen lig')}\n"
        f"{t['home']['name']} {g.get('home') or 0} - {g.get('away') or 0} {t['away']['name']}\n"
        f"🥅 {gol_satiri}\n"
        f"⏱ Şu an: {durum.get('elapsed')}'"
    )


def tur(sent):
    maclar = api_get("fixtures", live="all").get("response", [])
    kayitsiz = 0  # golu olup gol kaydi gelmemis canli mac
    for mac in maclar:
        kayitli = any(e.get("type") == "Goal" for e in mac.get("events") or [])
        if toplam_skor(mac) > 0 and not kayitli:
            kayitsiz += 1
        mid = f"af-{mac['fixture']['id']}"
        if mid in sent:
            continue
        goller = erken_goller(mac)
        if len(goller) >= GOL_ESIGI or skorla_erken_mi(mac):
            ad = f"{mac['teams']['home']['name']} - {mac['teams']['away']['name']}"
            if telegram_gonder(mesaj_olustur(mac, goller)):
                sent[mid] = time.time()
                sent = sent_kaydet(sent)
                log(f"BİLDİRİM: {ad}")
            else:
                log(f"Telegram hatasi: {ad}")
    log(f"{len(maclar)} canli mac tarandi (gol kaydi olmayan: {kayitsiz})")
    return sent


def hesap_durumu():
    try:
        d = api_get("status").get("response") or {}
        log(f"Plan: {d.get('subscription', {}).get('plan')}, gunluk sinir: {d.get('requests', {}).get('limit_day')}")
    except Exception as e:
        log(f"Hesap durumu alinamadi: {e}")


def main():
    if not API_KEY or not TOKEN or not CHAT_ID:
        sys.exit("API_FOOTBALL_KEY, TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID gerekli")
    if os.environ.get("TEST_MESAJI") == "true":
        ok = telegram_gonder("✅ Gol Alarmı çalışıyor (test mesajı)")
        log(f"Test mesaji: {'gonderildi' if ok else 'HATA'}")
    sent = sent_yukle()
    hesap_durumu()
    bitis = time.time() + LOOP_MINUTES * 60
    hata_sayisi = 0
    while True:
        try:
            sent = tur(sent)
            hata_sayisi = 0
        except Exception as e:  # ag hatasi vs. -> bir sonraki turda tekrar dene
            hata_sayisi += 1
            log(f"Hata: {e}")
            # Sessizce durmasin (kota doldu, abonelik bitti gibi)
            if hata_sayisi == UYARI_TUR:
                try:
                    telegram_gonder(f"⚠️ Gol Alarmı {UYARI_TUR} turdur maçları okuyamıyor, bildirim gelmeyebilir.\n{e}")
                except Exception as e2:
                    log(f"Uyari gonderilemedi: {e2}")
        if time.time() + POLL_SECONDS >= bitis:
            break
        time.sleep(POLL_SECONDS)
    sent_kaydet(sent)


if __name__ == "__main__":
    main()
