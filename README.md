# Gol Alarmı

Dünyadaki bütün liglerde (ESPN'nin kapsadığı ~220 lig) **ilk 20 dakikada 2 veya daha fazla gol** olan maçları Telegram'a bildirir. Her maç için tek bildirim gider.

## Nasıl çalışır
- `gol_alarmi.py` dakikada bir ESPN'nin açık skor servisinden canlı maçları çeker.
- Gol dakikalarına bakar: 20' veya öncesinde atılan gol sayısı 2'ye ulaştıysa mesaj atar.
- Kontrol geç kalsa bile (ör. 25. dakikada bakılsa) gol dakikalarına baktığı için kaçırmaz.
- ESPN'in gol dakikası vermediği maçlarda yedek kontrol çalışır: ilk yarıda, maç saati 1-20 arasındayken toplam skor 2 veya üstüyse bildirir. Bu yöntemde geç gelen skor kaçabilir, saati gelmeyen maçlar bildirilmez.
- GitHub Actions'ta ~5 saat 40 dk çalışır, sonra kendini yeniden başlatır. Böylece 7/24 açık kalır.

## Ayarlar (workflow `env` kısmı)
| Değişken | Varsayılan | Anlamı |
|---|---|---|
| `GOL_ESIGI` | 2 | En az kaç gol |
| `DAKIKA_SINIRI` | 20 | Kaçıncı dakikaya kadar |
| `POLL_SECONDS` | 60 | Kaç saniyede bir kontrol |

## Kurulum
1. GitHub'da **public** repo aç (public repolarda Actions dakikası sınırsız; private'ta ayda 2000 dk, 7/24 için yetmez).
2. Repo → Settings → Secrets and variables → Actions → şu iki secret'ı ekle:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Dosyaları yükle, Actions sekmesinden **Gol Alarmi → Run workflow** ile ilk kez başlat.

## Bilgisayarda deneme
```
set TELEGRAM_BOT_TOKEN=...
set TELEGRAM_CHAT_ID=...
set LOOP_MINUTES=0
python gol_alarmi.py
```
`LOOP_MINUTES=0` tek tur tarayıp çıkar.
