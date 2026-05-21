# 🔌 FIZIKSEL BAĞLANTI REHBERİ
## INF 208 — Tarım Deposu Projesi | Raspberry Pi 3

---

## ÖNEMLİ UYARILAR

⚠️  **YAPMAYIN:**
- HC-SR04 ECHO pinini direkt GPIO'ya BAĞLAMAYIN (5V → GPIO hasar!)
- Breadboard üzerinde güç vermeyin, önce bağlantıları kontrol edin
- PIR sensörünü 3.3V'a bağlamayın, 5V gerektirir

✅  **YAPIN:**
- Her bağlantıdan önce RPi'yi kapatın (sudo shutdown -h now)
- GPIO 4 (DHT11) ve GPIO 24 (HC-SR04 ECHO) doğru pinler
- Gerilim bölücü dirençleri doğru sırayla koy

---

## ADIM 1 — DHT11 Sıcaklık/Nem Sensörü

DHT11 sensörünüzde genellikle 3 pin vardır:
`[VCC] [DATA] [GND]`  veya  `[GND] [DATA] [VCC]`
(Üzerindeki yazılara bakın)

```
DHT11           Breadboard      RPi 3 Fiziksel Pin
────────────────────────────────────────────────────
VCC         →   breadboard  →  Pin 1  (3.3V)
DATA        →   breadboard  →  Pin 7  (GPIO 4)
GND         →   breadboard  →  Pin 6  (GND)

+ 10kΩ direnç: DHT11 DATA ↔ 3.3V arasına (pull-up)
```

Nasıl yerleştir:
1. DHT11'i breadboard'un soluna yerleştir (A1, B1, C1 satırı)
2. Kırmızı jumper: DHT11 VCC → RPi Pin 1
3. Sarı jumper: DHT11 DATA → RPi Pin 7
4. Siyah jumper: DHT11 GND → RPi Pin 6
5. 10kΩ direnç: DATA hattı ↔ 3.3V hattı arasına

---

## ADIM 2 — HC-SR04 Ultrasonik Sensör (GERİLİM BÖLÜCÜ ZORUNLU!)

```
HC-SR04         Breadboard / Direnç     RPi 3 Fiziksel Pin
───────────────────────────────────────────────────────────
VCC         →                       →  Pin 2  (5V)
GND         →                       →  Pin 9  (GND)
TRIG        →                       →  Pin 16 (GPIO 23)
ECHO        →   1kΩ → [bağlantı nokta] → Pin 18 (GPIO 24)
                       [bağlantı nokta] → 2kΩ → GND
```

Gerilim bölücü nasıl kurulur (breadboard):
```
HC-SR04 ECHO → jumper → breadboard E5
breadboard F5 → 1kΩ direnç → breadboard F8
breadboard E8 → jumper → RPi Pin 18 (GPIO 24)
breadboard F8'den ayrıca → 2kΩ direnç → GND hattı

Hesap: V_GPIO = 5V × 2kΩ/(1kΩ+2kΩ) = 3.33V ✓
```

---

## ADIM 3 — PIR Hareket Sensörü

PIR modülünde 3 pin var: `[VCC] [OUT] [GND]` (üstünde yazar)

```
PIR Sensör       Breadboard       RPi 3 Fiziksel Pin
─────────────────────────────────────────────────────
VCC          →                →  Pin 4  (5V)
OUT          →                →  Pin 11 (GPIO 17)
GND          →                →  Pin 14 (GND)
```

Not: Bazı PIR modüllerinde üstte hassasiyet ve gecikme potansiyometreleri var.
Her ikisini de orta konuma getir (saat 12 pozisyonu).

---

## ADIM 4 — 5V Röle Modülü

```
Röle Modülü      Breadboard       RPi 3 Fiziksel Pin
─────────────────────────────────────────────────────
VCC          →                →  Pin 2  (5V)
GND          →                →  Pin 25 (GND)
IN           →                →  Pin 12 (GPIO 18)
```

Rölenin çıkış terminallerine (COM, NO, NC) fan veya LED'i bağlayabilirsin.
Demo için: COM → GND, NO → LED katot, LED anot → 330Ω → 3.3V

---

## ADIM 5 — LED'ler

Her LED için 330Ω seri direnç zorunlu!

```
LED            Direnç         RPi Fiziksel Pin
────────────────────────────────────────────────
YEŞİL anot  →  330Ω       →  Pin 13 (GPIO 27)
YEŞİL katot →             →  Pin 20 (GND)

SARI anot   →  330Ω       →  Pin 15 (GPIO 22)
SARI katot  →             →  Pin 20 (GND)

KIRMIZI anot →  330Ω      →  Pin 22 (GPIO 25)
KIRMIZI katot →           →  Pin 20 (GND)
```

LED'in kısa bacağı (katot) = GND, uzun bacağı (anot) = pozitif

---

## ADIM 6 — Buzzer

```
Buzzer           Breadboard       RPi Fiziksel Pin
─────────────────────────────────────────────────────
+ (uzun bacak) →               →  Pin 32 (GPIO 12)
- (kısa bacak) →               →  Pin 34 (GND)
```

---

## ADIM 7 — Push Buton (Reset)

```
Buton            Direnç / Breadboard    RPi Fiziksel Pin
─────────────────────────────────────────────────────────
Uç 1         →                      →  Pin 29 (GPIO 5)
Uç 2         →                      →  Pin 30 (GND)
+ 10kΩ pull-up: GPIO 5 ↔ 3.3V arasına
```

---

## ÖZET PIN TABLOSU

```
RPi BCM  Fiziksel  Bileşen
───────  ────────  ─────────────────────
GPIO  4  Pin  7   DHT11 DATA
GPIO 17  Pin 11   PIR OUT
GPIO 18  Pin 12   RÖLE IN
GPIO 27  Pin 13   LED YEŞİL
GPIO 22  Pin 15   LED SARI
GPIO 23  Pin 16   HC-SR04 TRIG
GPIO 24  Pin 18   HC-SR04 ECHO (gerilim bölücü üzerinden)
GPIO 25  Pin 22   LED KIRMIZI
GPIO  5  Pin 29   PUSH BUTON
GPIO 12  Pin 32   BUZZER +
5V       Pin  2   HC-SR04 VCC, Röle VCC, PIR VCC
5V       Pin  4   (yedek güç)
3.3V     Pin  1   DHT11 VCC
GND      Pin  6   DHT11 GND
GND      Pin  9   HC-SR04 GND
GND      Pin 14   PIR GND
GND      Pin 20   LED'ler GND
GND      Pin 25   Röle GND
GND      Pin 30   Buton GND
GND      Pin 34   Buzzer -
```

---

## KURULUM VE ÇALIŞTIRMA (RPi Terminali)

Bağlantıları yaptıktan sonra RPi'yi aç ve terminalde:

```bash
# 1. Bağımlılıkları yükle
pip3 install RPi.GPIO adafruit-circuitpython-dht

# 2. Proje dizinine gir
cd tarim-depo-inf208

# 3. Ana sistemi çalıştır
python3 src/rtos_scheduler.py

# 4. WCET analizini ayrı terminalde çalıştır
python3 src/wcet_analysis.py

# 5. Değerlendirme grafiklerini üret
python3 src/evaluation.py
```

Logları görüntüle:
```bash
# Gerçek zamanlı sensör logu
tail -f logs/sensor_log.csv

# CPU sıcaklığı ölç (termal analiz için)
watch -n 5 vcgencmd measure_temp
```

---

## HATA GİDERME

| Sorun | Olası Neden | Çözüm |
|-------|------------|-------|
| DHT11 okuma hatası | Pull-up direnç eksik | 10kΩ ekle |
| HC-SR04 hep -1.0 | Gerilim bölücü yanlış | 1kΩ+2kΩ kontrol et |
| LED yanmıyor | Seri direnç eksik | 330Ω ekle |
| PIR sürekli tetikleniyor | Hassasiyet çok yüksek | Potansiyometreyi sola döndür |
| Röle tıklamıyor | Güç yetersiz | 5V pininden besle (3.3V değil) |
| ImportError: RPi.GPIO | Kütüphane yüklü değil | pip3 install RPi.GPIO |
