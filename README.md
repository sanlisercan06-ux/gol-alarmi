# Gol Alarmı

API-Football'un canlı verdiği bütün liglerde **ilk 12 dakikada 2 veya daha fazla gol** olan maçları, yalnızca gollü liglerde (son 60 günde maç başı en az 3,0 gol) Telegram'a bildirir. Her maç için tek bildirim gider.

## Nasıl çalışır
- `gol_alarmi.py` dakikada bir API-Football'dan (`fixtures?live=all`) canlı maçları çeker. Günde ~1.440 istek harcar.
- Gol dakikalarına bakar: 12' veya öncesinde atılan gol sayısı 2'ye ulaştıysa ve ligin gol ortalaması 3,0 veya üstüyse mesaj atar.
- Lig ortalamaları her çalışma başında son 60 günün biten maçlarından hesaplanır (~60 istek). 10'dan az maçı olan lig bildirilmez.
- Filtrenin nedeni: 20 dk kuralı günde ~40 (hafta sonu 75-89) bildirim üretiyordu. 60 günlük analizde filtre bildirimi ~5'te 1'e indirip ilk yarı 3+ golü %67'den %74'e çıkardı.
- Kontrol geç kalsa bile (ör. 25. dakikada bakılsa) gol dakikalarına baktığı için kaçırmaz.
- Gol kaydı gecikirse yedek kontrol çalışır: ilk yarıda, maç saati 1-12 arasındayken toplam skor 2 veya üstüyse bildirir.
- API art arda 30 tur okunamazsa (kota doldu, abonelik bitti gibi) Telegram'a bir kez uyarı gider.
- GitHub Actions'ta ~5 saat 40 dk çalışır, sonra kendini yeniden başlatır. Böylece 7/24 açık kalır.

## Ayarlar (workflow `env` kısmı)
| Değişken | Varsayılan | Anlamı |
|---|---|---|
| `GOL_ESIGI` | 2 | En az kaç gol |
| `DAKIKA_SINIRI` | 12 | Kaçıncı dakikaya kadar |
| `LIG_ORT_ESIGI` | 3.0 | Ligin son 60 gün maç başı gol ortalaması en az |
| `POLL_SECONDS` | 60 | Kaç saniyede bir kontrol |

## Kurulum
1. GitHub'da **public** repo aç (public repolarda Actions dakikası sınırsız; private'ta ayda 2000 dk, 7/24 için yetmez).
2. Repo → Settings → Secrets and variables → Actions → şu üç secret'ı ekle:
   - `API_FOOTBALL_KEY` (ücretli plan gerekir, ücretsiz planın 100 isteği yetmez)
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Dosyaları yükle, Actions sekmesinden **Gol Alarmi → Run workflow** ile ilk kez başlat.

## Bilgisayarda deneme
```
set API_FOOTBALL_KEY=...
set TELEGRAM_BOT_TOKEN=...
set TELEGRAM_CHAT_ID=...
set LOOP_MINUTES=0
python gol_alarmi.py
```
`LOOP_MINUTES=0` tek tur tarayıp çıkar.
