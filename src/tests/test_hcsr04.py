"""
HC-SR04 Ultrasonik Mesafe Sensörü Testi
Çalıştır: python3 src/tests/test_hcsr04.py
Beklenen çıktı: her 1 saniyede mesafe (cm)
"""
import RPi.GPIO as GPIO
import time

TRIG = 23
ECHO = 24

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.5)
    print(f"HC-SR04 başlatıldı — TRIG: GPIO{TRIG}, ECHO: GPIO{ECHO}\n")

def measure():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    timeout = time.monotonic() + 0.1
    while GPIO.input(ECHO) == 0:
        if time.monotonic() > timeout:
            return -1.0
    start = time.monotonic()

    timeout = time.monotonic() + 0.1
    while GPIO.input(ECHO) == 1:
        if time.monotonic() > timeout:
            return -1.0
    end = time.monotonic()

    return round((end - start) * 34300 / 2, 1)

try:
    setup()
    print(f"{'Deneme':<8} {'Mesafe':>12} {'Durum':>10}")
    print("-" * 34)
    for i in range(15):
        d = measure()
        if d < 0:
            print(f"{i+1:<8} {'TIMEOUT':>12}  sinyal alınamadı")
        elif d > 400:
            print(f"{i+1:<8} {d:>10.1f} cm  menzil dışı (>400cm)")
        else:
            bar = "█" * int(d / 10)
            print(f"{i+1:<8} {d:>10.1f} cm  {bar}")
        time.sleep(1)
    print("\nTest tamamlandı.")
except ImportError:
    print("RPi.GPIO bulunamadı. Kur: pip3 install RPi.GPIO")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
