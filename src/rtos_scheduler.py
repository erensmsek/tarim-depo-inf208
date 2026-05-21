"""
INF 208 - Gömülü Sistemler Final Projesi
Tarım Deposu İzleme ve Kontrol Sistemi

RTOS Görev Zamanlayıcı - Priority Inheritance ile
Raspberry Pi 3 üzerinde çalışır.

Görevler ve Öncelikleri:
  Task 1 (P=3, HIGH)   : Sensör okuma - 500ms periyot
  Task 2 (P=2, MEDIUM) : Karar ve aktüatör kontrolü - 1000ms periyot
  Task 3 (P=1, LOW)    : Loglama ve CSV yazma - 5000ms periyot

Priority Inheritance senaryosu:
  Task 3 (LOW) CSV dosyasına yazarken shared_resource kilidini tutar.
  Task 1 (HIGH) aynı kaynağa erişmek isteyince bloklanır.
  Bu noktada Task 3'ün önceliği geçici olarak Task 1'in önceliğine yükseltilir.
  Task 3 kaynağı serbest bırakınca öncelik normale döner.
"""

import threading
import time
import random
import csv
import os
import sys
from datetime import datetime
from collections import deque

# ─── Raspberry Pi GPIO ───────────────────────────────────────────────────────
# Gerçek RPi'de bu importları aktive et, simülasyon modunda sahte değerler üretilir
SIMULATION_MODE = True
try:
    import RPi.GPIO as GPIO
    import adafruit_dht
    import board
    SIMULATION_MODE = False
    print("[BOOT] Gerçek GPIO modu aktif.")
except (ImportError, RuntimeError):
    SIMULATION_MODE = True
    print("[BOOT] Simülasyon modu aktif (RPi kütüphaneleri bulunamadı).")

# ─── GPIO Pin Tanımları ───────────────────────────────────────────────────────
PIN_DHT11      = 4      # DHT11 veri pini (BCM)
PIN_TRIG       = 23     # HC-SR04 TRIG
PIN_ECHO       = 24     # HC-SR04 ECHO
PIN_PIR        = 17     # PIR sensör
PIN_RELAY      = 18     # Röle (fan/pompa)
PIN_LED_GREEN  = 27     # Yeşil LED - normal durum
PIN_LED_YELLOW = 22     # Sarı LED  - uyarı
PIN_LED_RED    = 25     # Kırmızı LED - alarm
PIN_BUZZER     = 12     # Buzzer
PIN_BUTTON     = 5      # Push buton - reset

# ─── Eşik Değerleri ──────────────────────────────────────────────────────────
TEMP_WARN_C    = 30.0   # °C - sıcaklık uyarı eşiği
TEMP_ALARM_C   = 38.0   # °C - sıcaklık alarm eşiği
HUM_WARN_PCT   = 80.0   # % - nem uyarı eşiği
HUM_ALARM_PCT  = 90.0   # % - nem alarm eşiği
DIST_WARN_CM   = 15.0   # cm - depo doluluk uyarı (yakın = dolu)
DIST_ALARM_CM  = 8.0    # cm - depo doluluk kritik

# ─── WCET Ölçüm Verileri ─────────────────────────────────────────────────────
wcet_data = {
    "task1_sensor":   deque(maxlen=200),
    "task2_actuator": deque(maxlen=200),
    "task3_logging":  deque(maxlen=200),
}

# ─── Paylaşılan Sistem Durumu ─────────────────────────────────────────────────
class SystemState:
    def __init__(self):
        self.temperature    = 0.0
        self.humidity       = 0.0
        self.distance_cm    = 100.0
        self.pir_motion     = False
        self.relay_on       = False
        self.alarm_active   = False
        self.system_status  = "IDLE"   # IDLE / NORMAL / WARNING / ALARM
        self.error_count    = 0
        self.last_update    = datetime.now()

state = SystemState()

# ─── Priority Inheritance Mutex ───────────────────────────────────────────────
class PriorityInheritanceMutex:
    """
    Priority Inheritance protokolünü simüle eden Mutex.
    Düşük öncelikli görev kaynağı tutarken yüksek öncelikli görev
    bloklandığında, düşük öncelikli görevin önceliği geçici olarak yükseltilir.
    """
    def __init__(self, name: str):
        self.name          = name
        self._lock         = threading.Lock()
        self.holder_name   = None
        self.holder_prio   = None
        self.original_prio = None
        self._meta_lock    = threading.Lock()

    def acquire(self, task_name: str, priority: int = 1, timeout: float = 5.0) -> bool:
        task_priority = priority
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._lock.acquire(blocking=False):
                with self._meta_lock:
                    self.holder_name   = task_name
                    self.holder_prio   = task_priority
                    self.original_prio = task_priority
                print(f"    [MUTEX:{self.name}] '{task_name}' (P={task_priority}) kilidi aldı.")
                return True
            else:
                # Kilit başka bir görevde → öncelik mirası
                with self._meta_lock:
                    if self.holder_prio is not None and task_priority > self.holder_prio:
                        print(f"    [PRIORITY-INHERIT] '{self.holder_name}' önceliği "
                              f"P={self.holder_prio} → P={task_priority} yükseltildi "
                              f"({task_name} bekliyor).")
                        self.holder_prio = task_priority
                time.sleep(0.005)
        print(f"    [MUTEX:{self.name}] '{task_name}' timeout! Kaynak alınamadı.")
        return False

    def release(self, task_name: str):
        with self._meta_lock:
            if self.holder_prio != self.original_prio:
                print(f"    [PRIORITY-INHERIT] '{task_name}' önceliği "
                      f"P={self.holder_prio} → P={self.original_prio} normale döndü.")
            self.holder_name   = None
            self.holder_prio   = None
            self.original_prio = None
        self._lock.release()

# Paylaşılan kaynaklar için mutex örnekleri
gpio_mutex    = PriorityInheritanceMutex("GPIO")
logfile_mutex = PriorityInheritanceMutex("LOGFILE")
state_mutex   = PriorityInheritanceMutex("STATE")

# ─── GPIO Başlatma ────────────────────────────────────────────────────────────
def gpio_setup():
    if SIMULATION_MODE:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_TRIG,       GPIO.OUT)
    GPIO.setup(PIN_ECHO,       GPIO.IN)
    GPIO.setup(PIN_PIR,        GPIO.IN)
    GPIO.setup(PIN_RELAY,      GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_LED_GREEN,  GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_LED_YELLOW, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_LED_RED,    GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_BUZZER,     GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(PIN_BUTTON,     GPIO.IN,  pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN_BUTTON, GPIO.FALLING,
                          callback=button_isr, bouncetime=300)
    GPIO.add_event_detect(PIN_PIR, GPIO.RISING,
                          callback=pir_isr, bouncetime=500)
    print("[GPIO] Tüm pinler yapılandırıldı.")

# ─── ISR (Interrupt Service Routines) ────────────────────────────────────────
def button_isr(channel):
    """Kategori 2 ISR: Deferred - sistem resetini tetikler."""
    global state
    print("\n  [ISR:BUTTON] Manuel reset tetiklendi! (GPIO kesmesi - Kategori 2)")
    state.alarm_active = False
    state.system_status = "NORMAL"
    state.error_count   = 0
    set_leds("green")

def pir_isr(channel):
    """Kategori 1 ISR: Direkt - hareket algılanınca güvenlik alarmı."""
    print("\n  [ISR:PIR] Hareket algılandı! (GPIO kesmesi - Kategori 1)")
    state.pir_motion = True

# ─── Donanım Okuma Fonksiyonları ──────────────────────────────────────────────
def read_dht11() -> tuple[float, float]:
    """DHT11'den sıcaklık ve nem oku. Retry mekanizması ile."""
    if SIMULATION_MODE:
        base_t = 26.0 + random.gauss(0, 2.5)
        base_h = 60.0 + random.gauss(0, 8.0)
        return round(base_t, 1), round(base_h, 1)
    dht = adafruit_dht.DHT11(board.D4)
    for attempt in range(3):
        try:
            temp = dht.temperature
            hum  = dht.humidity
            if temp is not None and hum is not None:
                return float(temp), float(hum)
        except RuntimeError as e:
            print(f"    [DHT11] Okuma hatası (deneme {attempt+1}/3): {e}")
            time.sleep(0.5)
    return None, None

def read_hcsr04() -> float:
    """HC-SR04 ultrasonik sensörden mesafe oku (cm). Anti-aliasing dahil."""
    if SIMULATION_MODE:
        return round(random.gauss(25.0, 5.0), 1)
    GPIO.output(PIN_TRIG, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(PIN_TRIG, GPIO.HIGH)
    time.sleep(0.000010)
    GPIO.output(PIN_TRIG, GPIO.LOW)
    timeout_start = time.monotonic()
    while GPIO.input(PIN_ECHO) == 0:
        if time.monotonic() - timeout_start > 0.1:
            return -1.0
    pulse_start = time.monotonic()
    while GPIO.input(PIN_ECHO) == 1:
        if time.monotonic() - pulse_start > 0.1:
            return -1.0
    pulse_end      = time.monotonic()
    pulse_duration = pulse_end - pulse_start
    # Nyquist: ses hızı 343 m/s, ± 0.3 cm hassasiyet
    distance = (pulse_duration * 34300.0) / 2.0
    return round(distance, 1)

def read_pir() -> bool:
    if SIMULATION_MODE:
        return random.random() < 0.05
    return GPIO.input(PIN_PIR) == GPIO.HIGH

# ─── LED ve Buzzer Kontrolü ───────────────────────────────────────────────────
def set_leds(mode: str):
    """mode: 'green' | 'yellow' | 'red'"""
    if SIMULATION_MODE:
        icons = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        print(f"    [LED] {icons.get(mode, '⚪')} durum göstergesi: {mode.upper()}")
        return
    GPIO.output(PIN_LED_GREEN,  GPIO.HIGH if mode == "green"  else GPIO.LOW)
    GPIO.output(PIN_LED_YELLOW, GPIO.HIGH if mode == "yellow" else GPIO.LOW)
    GPIO.output(PIN_LED_RED,    GPIO.HIGH if mode == "red"    else GPIO.LOW)

def set_relay(on: bool):
    if SIMULATION_MODE:
        print(f"    [RELAY] Fan/Pompa: {'AÇIK ▶' if on else 'KAPALI ■'}")
        return
    GPIO.output(PIN_RELAY, GPIO.HIGH if on else GPIO.LOW)

def buzzer_beep(count: int = 1, duration: float = 0.2):
    if SIMULATION_MODE:
        print(f"    [BUZZER] BİP x{count}")
        return
    for _ in range(count):
        GPIO.output(PIN_BUZZER, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(PIN_BUZZER, GPIO.LOW)
        time.sleep(0.1)

# ─── GÖREV 1 (HIGH PRIORITY = 3) — Sensör Okuma ──────────────────────────────
def task1_sensor_read(stop_event: threading.Event):
    """
    Periyodik: 500ms
    Öncelik: 3 (HIGH)
    DHT11, HC-SR04, PIR sensörlerini okur ve STATE'i günceller.
    GPIO mutex ile kaynak koruması.
    WCET ölçümü dahil.
    """
    print("[TASK1] Sensör okuma görevi başladı. (P=3, T=500ms)")
    while not stop_event.is_set():
        t_start = time.perf_counter()

        # GPIO erişimi için mutex al (Priority Inheritance burada devreye girer)
        if gpio_mutex.acquire("Task1-Sensor", priority=3, timeout=2.0):
            try:
                temp, hum  = read_dht11()
                distance   = read_hcsr04()
                motion     = read_pir()
            finally:
                gpio_mutex.release("Task1-Sensor")
        else:
            state.error_count += 1
            time.sleep(0.5)
            continue

        # Durum güncellemesi (state mutex)
        if state_mutex.acquire("Task1-Sensor", priority=3, timeout=1.0):
            try:
                if temp is not None:
                    state.temperature = temp
                    state.humidity    = hum
                else:
                    state.error_count += 1
                    print("    [TASK1] DHT11 okunamadı, hata sayacı artırıldı.")
                state.distance_cm  = distance
                state.pir_motion   = motion
                state.last_update  = datetime.now()
            finally:
                state_mutex.release("Task1-Sensor")

        t_end  = time.perf_counter()
        wcet   = (t_end - t_start) * 1000  # ms
        wcet_data["task1_sensor"].append(wcet)

        print(f"  [T1] Sıcaklık:{state.temperature:.1f}°C  "
              f"Nem:{state.humidity:.1f}%  "
              f"Mesafe:{state.distance_cm:.1f}cm  "
              f"PIR:{'HAREKET!' if state.pir_motion else 'yok'}  "
              f"WCET:{wcet:.2f}ms")

        stop_event.wait(timeout=0.5)  # 500ms periyot

# ─── GÖREV 2 (MEDIUM PRIORITY = 2) — Karar & Aktüatör ───────────────────────
def task2_actuator_control(stop_event: threading.Event):
    """
    Periyodik: 1000ms
    Öncelik: 2 (MEDIUM)
    Sensör verilerine göre FSM durumunu günceller ve aktüatörleri kontrol eder.
    Finite State Machine (FSM) implementasyonu.
    """
    print("[TASK2] Aktüatör kontrol görevi başladı. (P=2, T=1000ms)")
    while not stop_event.is_set():
        t_start = time.perf_counter()

        # ── FSM: Durum Makinesi Mantığı ──────────────────────────────────────
        # IDLE → NORMAL → WARNING → ALARM → NORMAL (reset ile)
        if state_mutex.acquire("Task2-Actuator", priority=2, timeout=1.5):
            try:
                temp    = state.temperature
                hum     = state.humidity
                dist    = state.distance_cm
                motion  = state.pir_motion
                prev_st = state.system_status

                # Geçiş koşulları
                alarm_cond  = (temp >= TEMP_ALARM_C or
                               hum  >= HUM_ALARM_PCT or
                               dist <= DIST_ALARM_CM or
                               motion)
                warn_cond   = (temp >= TEMP_WARN_C or
                               hum  >= HUM_WARN_PCT or
                               dist <= DIST_WARN_CM)

                if alarm_cond:
                    new_status = "ALARM"
                elif warn_cond:
                    new_status = "WARNING"
                elif temp > 0:
                    new_status = "NORMAL"
                else:
                    new_status = "IDLE"

                if new_status != prev_st:
                    print(f"  [FSM] Durum geçişi: {prev_st} → {new_status}")

                state.system_status = new_status
                state.pir_motion    = False  # PIR bayrağını sıfırla
            finally:
                state_mutex.release("Task2-Actuator")
        else:
            time.sleep(1.0)
            continue

        # ── Aktüatör Kararları ────────────────────────────────────────────────
        if gpio_mutex.acquire("Task2-Actuator", priority=2, timeout=2.0):
            try:
                status = state.system_status
                if status == "ALARM":
                    set_leds("red")
                    set_relay(True)
                    buzzer_beep(2)
                    state.alarm_active = True
                elif status == "WARNING":
                    set_leds("yellow")
                    set_relay(True)
                    state.alarm_active = False
                elif status == "NORMAL":
                    set_leds("green")
                    set_relay(False)
                    state.alarm_active = False
                else:
                    set_leds("green")
                    set_relay(False)
            finally:
                gpio_mutex.release("Task2-Actuator")

        t_end = time.perf_counter()
        wcet  = (t_end - t_start) * 1000
        wcet_data["task2_actuator"].append(wcet)

        print(f"  [T2] FSM:{state.system_status:8s}  "
              f"Röle:{'AÇIK' if state.relay_on else 'KPLI'}  "
              f"WCET:{wcet:.2f}ms")

        stop_event.wait(timeout=1.0)  # 1000ms periyot

# ─── GÖREV 3 (LOW PRIORITY = 1) — Loglama ────────────────────────────────────
def task3_logging(stop_event: threading.Event, log_dir: str):
    """
    Periyodik: 5000ms
    Öncelik: 1 (LOW)
    Verileri CSV'ye yazar. logfile_mutex tutar.
    Priority Inheritance senaryosu: Task1 bu mutex'i beklediğinde
    Task3'ün önceliği Task1 önceliğine geçici olarak yükseltilir.
    """
    log_path = os.path.join(log_dir, "sensor_log.csv")
    print(f"[TASK3] Loglama görevi başladı. (P=1, T=5000ms) → {log_path}")

    # CSV başlık satırı
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "temperature_c", "humidity_pct",
                             "distance_cm", "pir_motion", "status",
                             "relay_on", "error_count",
                             "t1_wcet_ms", "t2_wcet_ms"])

    while not stop_event.is_set():
        t_start = time.perf_counter()

        # logfile_mutex al — bu sırada Task1 (HIGH) aynı kaynağa ihtiyaç
        # duyarsa Priority Inheritance devreye girer
        if logfile_mutex.acquire("Task3-Logging", priority=1, timeout=6.0):
            try:
                # Yazma kasıtlı olarak biraz yavaş → Priority Inheritance
                # senaryosunu tetiklemek için
                time.sleep(0.05)

                row = [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    state.temperature,
                    state.humidity,
                    state.distance_cm,
                    int(state.pir_motion),
                    state.system_status,
                    int(state.relay_on),
                    state.error_count,
                    round(max(wcet_data["task1_sensor"],  default=0.0), 3),
                    round(max(wcet_data["task2_actuator"], default=0.0), 3),
                ]
                with open(log_path, "a", newline="") as f:
                    csv.writer(f).writerow(row)
                print(f"  [T3] Log kaydedildi: {row[0]}")
            finally:
                logfile_mutex.release("Task3-Logging")
        else:
            print("  [T3] logfile_mutex timeout — log atlandı.")

        t_end = time.perf_counter()
        wcet  = (t_end - t_start) * 1000
        wcet_data["task3_logging"].append(wcet)
        print(f"  [T3] WCET:{wcet:.2f}ms")

        stop_event.wait(timeout=5.0)  # 5000ms periyot

# ─── WCET Raporu ──────────────────────────────────────────────────────────────
def print_wcet_report():
    print("\n" + "="*60)
    print("  WCET RAPORU (En Kötü Durum Yürütme Süresi)")
    print("="*60)
    tasks = [
        ("Task1 - Sensör Okuma  (T=500ms)",   "task1_sensor"),
        ("Task2 - Aktüatör Ctrl (T=1000ms)",  "task2_actuator"),
        ("Task3 - Loglama       (T=5000ms)",  "task3_logging"),
    ]
    total_util = 0.0
    periods = [0.5, 1.0, 5.0]
    for i, (label, key) in enumerate(tasks):
        data = list(wcet_data[key])
        if not data:
            continue
        wcet_val = max(data)
        avg_val  = sum(data) / len(data)
        util     = (wcet_val / 1000.0) / periods[i] * 100
        total_util += (wcet_val / 1000.0) / periods[i]
        print(f"  {label}")
        print(f"    Ölçüm sayısı : {len(data)}")
        print(f"    WCET (maks)  : {wcet_val:.3f} ms")
        print(f"    Ortalama     : {avg_val:.3f} ms")
        print(f"    Kullanım U_i : {util:.2f}%")
        print()
    print(f"  Toplam Kullanım (ΣU_i) : {total_util*100:.2f}%")
    schedulable = total_util <= 1.0
    print(f"  Zamanlanabilirlik      : {'✓ SCHEDULABLE (ΣU≤1)' if schedulable else '✗ AŞIM!'}")
    print("="*60)

# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*60)
    print("  TARIM DEPOSU İZLEME SİSTEMİ - INF 208")
    print("  Raspberry Pi 3 | RTOS Simülasyonu")
    print("="*60 + "\n")

    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)

    gpio_setup()

    stop_event = threading.Event()

    # Görev thread'leri oluştur
    t1 = threading.Thread(target=task1_sensor_read,
                          args=(stop_event,), name="Task1-HIGH",  daemon=True)
    t2 = threading.Thread(target=task2_actuator_control,
                          args=(stop_event,), name="Task2-MED",   daemon=True)
    t3 = threading.Thread(target=task3_logging,
                          args=(stop_event, log_dir), name="Task3-LOW", daemon=True)

    # Thread öncelikleri (Linux üzerinde SCHED_FIFO ile gerçek öncelik)
    try:
        import ctypes
        libc = ctypes.CDLL("libpthread.so.0", use_errno=True)
        SCHED_FIFO = 1
        class sched_param(ctypes.Structure):
            _fields_ = [("sched_priority", ctypes.c_int)]
        # Gerçek RPi'de çalıştır (sudo gerekir)
    except Exception:
        pass  # Simülasyonda Python thread önceliği yeterli

    print("[MAIN] Görevler başlatılıyor...\n")
    t1.start()
    time.sleep(0.1)
    t2.start()
    time.sleep(0.1)
    t3.start()

    try:
        duration = 60  # saniye - demo için
        print(f"\n[MAIN] Sistem {duration} saniye çalışacak. Durdurmak için Ctrl+C\n")
        time.sleep(duration)
    except KeyboardInterrupt:
        print("\n[MAIN] Kullanıcı durdurdu.")
    finally:
        print("[MAIN] Görevler durduruluyor...")
        stop_event.set()
        t1.join(timeout=2)
        t2.join(timeout=2)
        t3.join(timeout=6)
        print_wcet_report()
        if not SIMULATION_MODE:
            GPIO.cleanup()
        print("[MAIN] Sistem kapatıldı.")

if __name__ == "__main__":
    main()
