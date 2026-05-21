# Tarım Deposu İzleme ve Kontrol Sistemi
## INF 208 — Gömülü Sistemler Final Projesi
**Türk-Alman Üniversitesi | Prof. Dr. Murat Beken**

---

## Proje Özeti

Raspberry Pi 3 tabanlı, gerçek zamanlı tarım deposu izleme sistemi.
Sıcaklık, nem ve doluluk seviyesini sürekli ölçer; eşikler aşılınca
fan/pompayı otomatik devreye alır, LED ve buzzer ile alarm verir.

---

## Donanım Bağlantıları

```
RPi GPIO  Bileşen           Açıklama
────────  ────────────────  ─────────────────────────────────
GPIO  4   DHT11 DATA        Sıcaklık & Nem sensörü
GPIO 23   HC-SR04 TRIG      Ultrasonik mesafe - TRIG
GPIO 24   HC-SR04 ECHO      Ultrasonik mesafe - ECHO (→ 1kΩ+2kΩ gerilim bölücü!)
GPIO 17   PIR DATA          Hareket sensörü
GPIO 18   RÖLE IN           5V Röle kontrol girişi
GPIO 27   LED YEŞİL         Normal durum göstergesi (330Ω seri)
GPIO 22   LED SARI          Uyarı göstergesi (330Ω seri)
GPIO 25   LED KIRMIZI       Alarm göstergesi (330Ω seri)
GPIO 12   BUZZER +          Aktif buzzer pozitif ucu
GPIO  5   PUSH BUTON        Manuel reset (10kΩ pull-up, GND'e bağlı uç)
3.3V      DHT11 VCC, PIR VCC
5V        HC-SR04 VCC, RÖLE VCC
GND       Tüm GND uçları
```

> ⚠️  **ÖNEMLİ**: HC-SR04 ECHO pini 5V çıkış verir.
> RPi GPIO 3.3V toleranslıdır → 1kΩ + 2kΩ gerilim bölücü kullan!

---

## Kurulum

```bash
# 1. Sistem güncellemesi (RPi'de)
sudo apt update && sudo apt upgrade -y

# 2. Gerekli paketler
sudo apt install python3-pip python3-dev -y
pip3 install RPi.GPIO adafruit-circuitpython-dht matplotlib numpy

# 3. Projeyi indir / kopyala
git clone https://github.com/erensmsek/tarim-depo-inf208
cd tarim-depo-inf208
```

---

## Çalıştırma

```bash
# Ana RTOS sistemi (60 saniye demo)
python3 src/rtos_scheduler.py

# WCET analizi
python3 src/wcet_analysis.py

# Enerji + Pareto grafiklerini üret
python3 src/evaluation.py
```

---

## Proje Yapısı

```
tarim_depo_projesi/
├── src/
│   ├── rtos_scheduler.py   # Ana RTOS görevi (Priority Inheritance dahil)
│   ├── evaluation.py       # Enerji, termal, Pareto analizi
│   └── wcet_analysis.py    # WCET ölçümü ve schedulability testi
├── logs/
│   ├── sensor_log.csv      # Otomatik oluşturulur
│   ├── thermal_log.csv     # Otomatik oluşturulur
│   ├── wcet_results.csv    # Otomatik oluşturulur
│   └── evaluation_plots.png
├── diagrams/               # StateChart ve Petri ağı resimleri
├── README.md
└── requirements.txt
```

---

## Değerlendirme Kriterleri (INF 208)

| Kriter                     | Karşılanıyor mu? | Dosya / Bölüm            |
|---------------------------|-----------------|--------------------------|
| ≥2 Sensör                 | ✓ DHT11 + HC-SR04 + PIR | rtos_scheduler.py   |
| ≥1 Aktüatör               | ✓ Röle (fan/pompa)      | rtos_scheduler.py   |
| FSM / Karar algoritması   | ✓ 4-durumlu FSM         | task2_actuator_control() |
| RTOS görev zamanlaması    | ✓ 3 periyodik görev     | rtos_scheduler.py   |
| Priority Inheritance      | ✓ PriorityInheritanceMutex | rtos_scheduler.py |
| ISR yönetimi              | ✓ Buton (Kat.2) + PIR (Kat.1) | gpio_setup()   |
| WCET analizi              | ✓ 200 iterasyon         | wcet_analysis.py    |
| Enerji analizi (CMOS)     | ✓ P=αCV²f               | evaluation.py       |
| Termal modelleme          | ✓ Rth hesabı            | evaluation.py       |
| Pareto optimizasyonu      | ✓ Yanıt vs. Enerji      | evaluation.py       |
| StateChart modeli         | ✓ diagrams/ klasörü     | rapor ekinde        |
| Petri Ağı modeli          | ✓ diagrams/ klasörü     | rapor ekinde        |
| CSV loglama               | ✓ logs/ klasörü         | task3_logging()     |
| Git versiyon kontrolü     | ✓ public repo           | —                   |

---

## Lisans

MIT License — Açık kaynak (INF 208 Bonus kriteri)
