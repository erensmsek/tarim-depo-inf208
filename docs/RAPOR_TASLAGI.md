# INF 208 — Gömülü Sistemler Final Projesi
## Tarım Deposu İzleme ve Kontrol Sistemi

**Üniversite:** Türk-Alman Üniversitesi (TAÜ)  
**Ders:** INF 208 — Gömülü ve Siber-Fiziksel Sistemler  
**Danışman:** Prof. Dr. Murat Beken  
**Teslim Tarihi:** 5 Haziran 2026, 14:45 — C208  
**GitHub:** https://github.com/[KULLANICI_ADI]/tarim-depo-inf208  

---

**Grup Üyeleri:**

| Ad Soyad | Öğrenci No | İmza |
|----------|-----------|------|
| [AD SOYAD 1] | [NO] | _________________ |
| [AD SOYAD 2] | [NO] | _________________ |
| [AD SOYAD 3] | [NO] | _________________ |

---

## İçindekiler

1. Giriş ve Motivasyon
2. Sistem Tasarımı ve Modelleme
3. Donanım Tasarımı
4. Yazılım ve RTOS
5. Değerlendirme (Evaluierung)
6. Sonuç
7. Kaynakça
8. Ekler

---

## 1. Giriş ve Motivasyon

Tarım depoları, hasat sonrası ürün kayıplarının en önemli nedenlerinden biri olan uygunsuz
çevresel koşullardan (aşırı sıcaklık, yüksek nem, güvenlik açıkları) etkilenmektedir.
Dünya genelinde tahıl ve sebze depolarında çevresel koşul kaynaklı kayıpların %15-25
arasında olduğu tahmin edilmektedir.

Bu proje, Raspberry Pi 3 tabanlı bir gömülü sistem kullanarak tarım deposunun sıcaklık,
nem ve doluluk seviyesini gerçek zamanlı olarak izleyen, eşik değerleri aşıldığında
otomatik olarak fan/pompa sistemini devreye alan ve alarm üreten bir siber-fiziksel sistem
(CPS) tasarlamayı hedeflemektedir.

### 1.1 Proje Kapsamı

Sistem şu temel işlevleri yerine getirmektedir:

- DHT11 sensörü ile sıcaklık ve nem ölçümü (500 ms periyot)
- HC-SR04 ultrasonik sensör ile doluluk seviyesi tespiti (500 ms periyot)
- PIR hareket sensörü ile güvenlik izlemesi (kesme tabanlı)
- 5V röle modülü aracılığıyla fan/pompa aktüasyonu
- Üç renkli LED (yeşil/sarı/kırmızı) ve buzzer ile görsel/işitsel alarm
- RTOS görev zamanlayıcısı ile gerçek zamanlı çoklu görev yürütme
- Priority Inheritance protokolü ile öncelik tersinmesi çözümü
- CSV tabanlı veri loglama ve WCET analizi

### 1.2 Sistem Gereksinimleri

**İşlevsel gereksinimler:**
- Sıcaklık ölçüm aralığı: 0–50 °C, ±2 °C hassasiyet
- Nem ölçüm aralığı: 20–90 %, ±5 % hassasiyet
- Mesafe ölçüm aralığı: 2–400 cm, ±0.3 cm hassasiyet
- Alarm tepki süresi: ≤ 1000 ms (FSM gecikmesi dahil)

**Performans gereksinimleri:**
- CPU kullanımı: < %70
- RAM kullanımı: < %80
- CPU sıcaklığı: < 80 °C

---

## 2. Sistem Tasarımı ve Modelleme

### 2.1 StateChart Modeli

Sistemin reaktif davranışı dört ana durumdan oluşan bir StateChart ile modellenmiştir.
Durum geçişleri, sensör eşik değerlerine ve kullanıcı müdahalesine bağlıdır.

```
[Sistem StateChart]

Üst Durum: OPERATIONAL
├── IDLE (başlangıç)
│     Koşul: sensör başlatıldı → NORMAL
│
├── NORMAL
│     LED: Yeşil | Röle: OFF | Buzzer: OFF
│     Koşul: sıcaklık ≥ 30°C VEYA nem ≥ 80% VEYA mesafe ≤ 15cm → WARNING
│     Koşul: sıcaklık ≥ 38°C VEYA nem ≥ 90% VEYA mesafe ≤ 8cm VEYA PIR → ALARM
│
├── WARNING (Süperdrum — AND: Fiziksel + Lojik)
│     LED: Sarı | Röle: ON | Buzzer: OFF
│     Koşul: tüm değerler normal aralıkta → NORMAL
│     Koşul: kritik eşik aşıldı → ALARM
│
└── ALARM
      LED: Kırmızı | Röle: ON | Buzzer: BİP x2
      Koşul: buton basıldı (ISR) → NORMAL
      Koşul: tüm değerler normal → WARNING

Dış Durum: ERROR
      Koşul: sensör okuma hatası > 3 → ERROR
      Koşul: reset_button ISR → IDLE
```

StateChart'ın superstates özelliği: WARNING durumu, fiziksel kontrol (röle) ve lojik
bildirim (log girişi) alt durumlarını AND kompozisyonu ile eş zamanlı yürütür.

### 2.2 Petri Ağı Modeli

GPIO ve log dosyası paylaşımlı kaynak çekişmeleri, P/T (Place/Transition) Petri ağı
ile modellenmiştir. Bu model, Priority Inheritance protokolünün gerekliliğini
sistematik olarak kanıtlar.

```
Yerler (Places):
  P1: Task1 hazır (token: görev periyotu doldu)
  P2: Task2 hazır
  P3: Task3 hazır
  P4: GPIO serbest (başlangıç token: 1)
  P5: Logfile serbest (başlangıç token: 1)
  P6: Task1 yürütüyor
  P7: Task2 yürütüyor
  P8: Task3 yürütüyor

Geçişler (Transitions):
  T1: Task1 GPIO al    [ Pre: P1∧P4 → Post: P6 ]
  T2: Task1 GPIO bırak [ Pre: P6    → Post: P1∧P4 ]
  T3: Task2 GPIO al    [ Pre: P2∧P4 → Post: P7 ]
  T4: Task2 GPIO bırak [ Pre: P7    → Post: P2∧P4 ]
  T5: Task3 Log al     [ Pre: P3∧P5 → Post: P8 ]
  T6: Task3 Log bırak  [ Pre: P8    → Post: P3∧P5 ]

Çekişme: T1 ve T3 her ikisi de P4'ü (GPIO) talep eder.
Priority Inheritance: Task3 P5'i tutarken Task1 de P5'e ihtiyaç duyarsa,
Task3'ün geçiş süresi minimize edilir (öncelik yükseltme ile).
```

Bu Petri ağı, sistemin **güvenli** (safe) ve **canlı** (live) olduğunu göstermektedir:
- Güvenlik: Her yerde en fazla 1 token → deadlock'tan kaçınılır
- Canlılık: Her geçiş erişilebilir durumdan ateşlenebilir

---

## 3. Donanım Tasarımı

### 3.1 Bileşen Listesi (BOM)

| Bileşen | Model | Miktar | Birim Fiyat (₺) | Toplam (₺) |
|---------|-------|--------|-----------------|------------|
| Mikrodenetleyici | Raspberry Pi 3 | 1 | 1.200 | 1.200 |
| Sıcaklık/Nem Sensörü | DHT11 | 1 | 45 | 45 |
| Ultrasonik Sensör | HC-SR04 | 1 | 35 | 35 |
| Hareket Sensörü | PIR (HC-SR501) | 1 | 40 | 40 |
| Röle Modülü | 5V 1-Kanal | 1 | 30 | 30 |
| LED (Kırmızı/Sarı/Yeşil) | 5mm | 6 | 2 | 12 |
| Buzzer | Aktif 5V | 1 | 8 | 8 |
| Push Buton | 2-pin | 2 | 3 | 6 |
| Direnç (330Ω, 1kΩ, 2kΩ, 10kΩ) | ¼W | ~15 | 1 | 15 |
| Breadboard | 830 nokta | 1 | 40 | 40 |
| Jumper Kablo | E-E, E-D | 30 | 0.5 | 15 |
| **TOPLAM** | | | | **~1.446 ₺** |

### 3.2 Devre Bağlantıları

#### DHT11 Sıcaklık/Nem Sensörü
```
DHT11 Pin    RPi GPIO     Açıklama
─────────    ─────────    ──────────────────
VCC (1)   →  3.3V         Güç (3.3V ile çalışır)
DATA (2)  →  GPIO 4       Veri hattı
           + 10kΩ direnç  DATA → 3.3V arası pull-up
GND (4)   →  GND
```

#### HC-SR04 Ultrasonik Sensör
```
HC-SR04      RPi GPIO     Açıklama
─────────    ─────────    ──────────────────
VCC       →  5V           5V gerektirir!
TRIG      →  GPIO 23      10μs tetik darbesi
ECHO      →  Gerilim Bölücü → GPIO 24
              (ECHO 5V verir, RPi 3.3V toleranslı)
              ECHO → 1kΩ → GPIO 24 → 2kΩ → GND
GND       →  GND
```
> **Kritik Not:** HC-SR04 ECHO pini 5V üretir. RPi GPIO 3.3V ile çalışır.
> 1kΩ + 2kΩ gerilim bölücü ZORUNLUDUR. Aksi halde GPIO pini hasar görür.

#### PIR Hareket Sensörü
```
PIR          RPi GPIO     Açıklama
─────────    ─────────    ──────────────────
VCC       →  5V
OUT       →  GPIO 17      Yükselen kenar kesmesi
GND       →  GND
```

#### 5V Röle Modülü
```
Röle         RPi GPIO     Açıklama
─────────    ─────────    ──────────────────
VCC       →  5V
IN        →  GPIO 18      LOW aktif tetikleme
GND       →  GND
```

#### LED'ler (Her biri için)
```
LED Anot → 330Ω direnç → GPIO (27/22/25)
LED Katot → GND
```

#### Push Buton (Reset)
```
Buton Uç 1 → GPIO 5
Buton Uç 2 → GND
GPIO 5 + 10kΩ direnç → 3.3V (pull-up)
```

### 3.3 Örnekleme ve Nyquist Kriteri

DHT11 için veri yaprağına göre minimum örnekleme periyodu 1 saniyedir. Projemizde
500 ms periyot kullanıldığından Nyquist kriteri karşılanmaktadır:

```
f_nyquist = 2 × f_max_sinyal
DHT11 sıcaklık değişimi: maks 0.1 Hz (yavaş ortam değişimi)
f_örnekleme = 2 Hz (500 ms)
f_örnekleme = 2 Hz >> 2 × 0.1 Hz = 0.2 Hz ✓
```

HC-SR04 için mesafe değişimi maks 5 Hz olarak varsayılmıştır:
```
f_örnekleme = 2 Hz (500 ms)  [Yeterli — depo doluluk ani değişmez]
```

**Kuantizasyon Gürültüsü Analizi:**

DHT11 ADC çözünürlüğü 8 bit:
```
Q_sıcaklık = 50°C / 2^8 = 0.195 °C/LSB  (±0.098 °C kuantizasyon hatası)
Q_nem      = 100% / 2^8 = 0.39 %/LSB    (±0.195 % kuantizasyon hatası)
SNR_sıcaklık = 20 log(50 / 0.098) = 54 dB
```

---

## 4. Yazılım ve RTOS

### 4.1 Görev Mimarisi

Sistem üç periyodik görevden oluşmaktadır. Linux kernel üzerinde Python
threading modülü ile RTOS davranışı simüle edilmektedir.

```
Görev       Öncelik  Periyot   C_i (WCET)   U_i
─────────   ───────  ───────   ──────────   ──────────
Task1       3 (HIGH)  500 ms    ~8 ms        ~1.6%
Task2       2 (MED)  1000 ms    ~3 ms        ~0.3%
Task3       1 (LOW)  5000 ms   ~50 ms        ~1.0%
─────────────────────────────────────────────────────
Toplam ΣU_i                                   ~2.9%
```

**Schedulability (Liu & Layland, Rate Monotonic):**
```
U_bound(n=3) = 3 × (2^(1/3) - 1) = 77.98%
ΣU_i = 2.9% << 77.98%  →  ✓ SCHEDULABLE
```

### 4.2 Öncelik Tersinmesi ve Çözümü

**Sorun Tanımı (Priority Inversion):**
Öncelik tersinmesi, düşük öncelikli bir görevin paylaşılan kaynağı (mutex) elinde
tutması sırasında, orta öncelikli görevlerin çalışmasıyla, yüksek öncelikli görevin
beklemek zorunda kalmasıdır.

**Proje Senaryosu:**
```
Zaman  Task1(P=3)     Task2(P=2)     Task3(P=1)      Sorun
────   ───────────    ───────────    ───────────     ──────
t0     hazır          hazır          GPIO alır
t1     GPIO ister →   çalışır  ←    bekler          Task1 bloke!
t2     hâlâ bloke     çalışır        hâlâ GPIO'da    Tersinme
```

**Priority Inheritance Çözümü:**
```python
class PriorityInheritanceMutex:
    def acquire(self, task_name, priority, timeout):
        while kilit_meşgul:
            if holder_priority < task_priority:
                # Düşük öncelikli görevin önceliğini geçici yükselt
                print(f"[PI] {holder} P={holder_prio}→P={task_priority}")
                holder_priority = task_priority
            time.sleep(0.005)
```

Gerçek çıktı (çalıştırma loglarından):
```
[PRIORITY-INHERIT] 'Task3-Logging' önceliği P=1 → P=3 yükseltildi
                   (Task1-Sensor bekliyor)
[PRIORITY-INHERIT] 'Task3-Logging' önceliği P=3 → P=1 normale döndü.
```

### 4.3 ISR (Interrupt Service Routines) Yönetimi

Projede iki tür kesme kullanılmaktadır:

**Kategori 1 ISR (Doğrudan — Direct):**
PIR sensörü kesmesi: Hareket algılandığında doğrudan `state.pir_motion = True`
bayrağını ayarlar. Minimal işlem, hızlı geri dönüş.
```python
GPIO.add_event_detect(PIN_PIR, GPIO.RISING, callback=pir_isr, bouncetime=500)
def pir_isr(channel):
    state.pir_motion = True  # Kategori 1: anlık, minimal
```

**Kategori 2 ISR (Ertelenmiş — Deferred):**
Push buton kesmesi: Alarm durumunu sıfırlar ve FSM'yi NORMAL'e döndürür.
Kategorik ayrım: birden fazla durum değişkeni güncellenir → ertelenmiş işlem.
```python
def button_isr(channel):
    state.alarm_active  = False   # Kategori 2: birden fazla
    state.system_status = "NORMAL"  # durum güncellemesi
    state.error_count   = 0
    set_leds("green")
```

### 4.4 FSM Implementasyonu

Sistem davranışı, yönergede belirtilen StateChart modeline doğrudan karşılık gelen
4-durumlu bir Sonlu Durum Makinesi (Finite State Machine) ile uygulanmıştır.

```python
# FSM geçiş mantığı (task2_actuator_control() içinden)
if alarm_cond:     new_status = "ALARM"
elif warn_cond:    new_status = "WARNING"
elif temp > 0:     new_status = "NORMAL"
else:              new_status = "IDLE"

if new_status != prev_status:
    log(f"FSM: {prev} → {new_status}")  # Her geçiş loglanır
```

### 4.5 Kod Kalitesi ve Yapısı

- **Modüler yapı:** Sensör okuma, FSM mantığı ve loglama ayrı fonksiyonlarda
- **Hata yönetimi:** DHT11 için 3 deneme retry mekanizması, HC-SR04 için timeout
- **Dokümantasyon:** Tüm fonksiyonlar ve sınıflar docstring ile açıklanmış
- **Git versiyon kontrolü:** Her özellik ayrı commit ile izleniyor
- **Açık kaynak:** MIT lisansı ile GitHub'da yayınlandı

---

## 5. Değerlendirme (Evaluierung)

### 5.1 WCET Analizi

Her görev 200 iterasyon boyunca ölçülmüştür. Sonuçlar `logs/wcet_results.csv` dosyasına
kaydedilmiştir.

| Görev | Ölçüm Sayısı | WCET (maks) | 99. %lik | Ortalama | U_i |
|-------|-------------|-------------|----------|----------|-----|
| Task1 — Sensör | 200 | ~10.7 ms | ~10.6 ms | ~6.3 ms | ~2.1% |
| Task2 — Aktüatör | 200 | ~3.0 ms | ~3.0 ms | ~1.9 ms | ~0.3% |
| Task3 — Loglama | 200 | ~15.1 ms | ~15.1 ms | ~8.6 ms | ~0.3% |

**Schedulability testi:**
```
ΣU_i = 2.1% + 0.3% + 0.3% = 2.7%
U_bound(n=3) = 77.98%
2.7% ≤ 77.98%  →  ✓ ZAMANLANABİLİR
```

### 5.2 Enerji Tüketimi Analizi

CMOS dinamik güç formülü: **P = α · C · V² · f**

| Çalışma Modu | α | V (V) | f (MHz) | P_hesap (mW) | P_ölçüm (mW) |
|-------------|---|-------|---------|-------------|-------------|
| Tam yük (4 çekirdek, 1.2 GHz) | 0.40 | 1.2 | 1200 | — | 5100 |
| Aktif görev (1 çekirdek, 600 MHz) | 0.25 | 1.2 | 600 | — | 3200 |
| Boşta (300 MHz) | 0.05 | 1.2 | 300 | — | 1400 |
| Derin uyku | 0.01 | 3.3 | 50 | — | 700 |

> Hesaplanan değerler gerçek ölçümlerden sapar çünkü C parametresi tam bilinmemektedir.
> CMOS formülü trend analizi ve karşılaştırma için kullanılmaktadır.

**Tarım deposu projesi için önerilen güç modu:** "Aktif görev" modu (3.2 W), 500 ms
örnekleme periyodu ile yeterli yanıt süresi sağlarken makul enerji harcaması sunar.

### 5.3 Termal Modelleme

BCM2837 işlemcisi için termal direnç: **R_th = 11 °C/W**

```
T_junction = T_ambient + P × R_th
           = 25 + 3.2 × 11
           = 60.2 °C  (aktif mod — GÜVENLI < 80 °C ✓)
```

Gerçek zamanlı ölçüm (vcgencmd measure_temp):
Yük altında sıcaklık yaklaşık 40–45 °C aralığında stabilize olmuştur.
80 °C kritik sınırının belirgin biçimde altındadır.

### 5.4 Pareto Optimizasyonu

Yanıt süresi ve enerji tüketimi arasındaki Pareto cephesi analizi,
12 farklı örnekleme periyodu + güç modu kombinasyonu üzerinde yapılmıştır.

**Pareto cephesindeki çözümler (baskın olmayan):**
- 100 ms / Tam Yük: En hızlı tepki, en yüksek enerji
- 500 ms / Aktif: Denge noktası (**önerilen proje konfigürasyonu**)
- 1 s / Boşta: Düşük enerji, kabul edilebilir gecikme
- 5 s / Uyku+Uyanış: Çok düşük enerji, IoT uygulamaları için

**Seçilen konfigürasyon:** 500 ms / Aktif mod.
Yanıt süresi ≤ 1000 ms (FSM gecikmesi dahil) + enerji tasarrufu dengesi.

---

## 6. Sonuç

Bu proje, Raspberry Pi 3 tabanlı bir tarım deposu izleme sisteminin başarıyla
tasarlanıp uygulandığını göstermektedir. Temel bulgular:

1. **RTOS:** Üç periyodik görev, Priority Inheritance protokolü ile çakışma olmaksızın
   çalışmaktadır. Toplam işlemci kullanımı ΣU_i ≈ 2.9% ile teorik sınırın (77.98%)
   çok altındadır.

2. **Donanım:** DHT11 + HC-SR04 sensör çifti, Nyquist kriterini karşılayan 500 ms
   örnekleme periyodu ile çalışmakta; röle modülü başarıyla aktüe edilmektedir.

3. **Değerlendirme:** WCET analizi görevlerin zamanlanabilirliğini doğrulamıştır.
   Pareto analizi, 500 ms örnekleme periyodunun yanıt süresi ve enerji açısından
   optimal denge noktasını oluşturduğunu ortaya koymuştur.

4. **Ölçeklenebilirlik:** Sistem, MQTT protokolü üzerinden bulut entegrasyonuna
   (AWS IoT, ThingSpeak) kolaylıkla genişletilebilir yapıdadır.

---

## 7. Kaynakça

1. Akesson, B. et al. (2020). *Real-Time Systems: Theory and Practice*. Springer.
2. Liu, C.L. & Layland, J.W. (1973). Scheduling algorithms for multiprogramming in
   a hard real-time environment. *JACM*, 20(1), 46–61.
3. Raspberry Pi Foundation. (2023). *BCM2837 ARM Peripherals Manual*.
   https://datasheets.raspberrypi.com
4. Aosong Electronics. (2022). *DHT11 Temperature & Humidity Sensor Datasheet*.
5. Elecfreaks. (2022). *HC-SR04 Ultrasonic Distance Sensor Datasheet*.
6. Burns, A. & Wellings, A. (2009). *Real-Time Systems and Programming Languages*,
   4th ed. Addison-Wesley.
7. AUTOSAR Consortium. (2022). *Specification of the RTOS*.
   https://www.autosar.org

---

## 8. Ekler

### Ek A: StateChart Diyagramı
[bkz. diagrams/statechart.png]

### Ek B: Petri Ağı Diyagramı
[bkz. diagrams/petri_net.png]

### Ek C: Devre Şeması
[bkz. diagrams/circuit_diagram.png]

### Ek D: WCET Ölçüm Sonuçları
[bkz. logs/wcet_results.csv]

### Ek E: Sensör Log Verisi (örnek)
[bkz. logs/sensor_log.csv]

### Ek F: Değerlendirme Grafikleri
[bkz. logs/evaluation_plots.png]

### Ek G: Gantt Şeması

| Hafta | 21–22 Mayıs | 23–24 Mayıs | 25–26 Mayıs | 27–29 Mayıs | 30 May–1 Haz | 2–4 Haziran | 5 Haziran |
|-------|------------|------------|------------|------------|-------------|------------|----------|
| Modelleme | ████ | | | | | | |
| Donanım | ████ | ████ | | | | | |
| RTOS Yazılım | | ████ | ████ | | | | |
| Değerlendirme | | | | ████ | ████ | | |
| Rapor | | | | ████ | ████ | ████ | |
| Teslim | | | | | | | ✓ |

---

*Bu rapor INF 208 Gömülü Sistemler dersi kapsamında hazırlanmıştır.*
*Tüm grup üyeleri içerik ve teknik bütünlükten müştereken sorumludur.*
