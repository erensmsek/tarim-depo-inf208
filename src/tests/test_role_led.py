"""
Röle + LED + Buzzer Testi
Çalıştır: python3 src/tests/test_role_led.py
Beklenen çıktı: röle tıklar, LED'ler sırayla yanar, buzzer bip yapar
"""
import RPi.GPIO as GPIO
import time

RELAY       = 18
LED_GREEN   = 27
LED_YELLOW  = 22
LED_RED     = 25
BUZZER      = 12

PINS_OUT = [RELAY, LED_GREEN, LED_YELLOW, LED_RED, BUZZER]

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for p in PINS_OUT:
        GPIO.setup(p, GPIO.OUT, initial=GPIO.LOW)
    print("Pinler hazır.\n")

def test_leds():
    print("── LED testi ──")
    for pin, renk in [(LED_GREEN, "YEŞİL"), (LED_YELLOW, "SARI"), (LED_RED, "KIRMIZI")]:
        print(f"  {renk} LED yanıyor...")
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.3)
    print("  Tüm LED'ler birden...")
    for p in [LED_GREEN, LED_YELLOW, LED_RED]:
        GPIO.output(p, GPIO.HIGH)
    time.sleep(1.5)
    for p in [LED_GREEN, LED_YELLOW, LED_RED]:
        GPIO.output(p, GPIO.LOW)
    print("  LED testi bitti.\n")

def test_relay():
    print("── Röle testi ──")
    print("  Röle AÇILIYOR (tık sesi duymalısın)...")
    GPIO.output(RELAY, GPIO.HIGH)
    time.sleep(2)
    print("  Röle KAPANIYOR...")
    GPIO.output(RELAY, GPIO.LOW)
    time.sleep(0.5)
    print("  Röle testi bitti.\n")

def test_buzzer():
    print("── Buzzer testi ──")
    for i in range(3):
        print(f"  BİP {i+1}")
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.3)
    print("  Buzzer testi bitti.\n")

def test_alarm_senaryosu():
    print("── Alarm senaryosu (ALARM durumu simülasyonu) ──")
    print("  Kırmızı LED + Röle + Buzzer birlikte...")
    GPIO.output(LED_RED,  GPIO.HIGH)
    GPIO.output(RELAY,    GPIO.HIGH)
    for _ in range(2):
        GPIO.output(BUZZER, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BUZZER, GPIO.LOW)
        time.sleep(0.2)
    time.sleep(1)
    GPIO.output(LED_RED, GPIO.LOW)
    GPIO.output(RELAY,   GPIO.LOW)
    print("  Alarm senaryosu bitti.\n")

try:
    setup()
    test_leds()
    test_relay()
    test_buzzer()
    test_alarm_senaryosu()
    print("Tüm testler başarılı!")
except ImportError:
    print("RPi.GPIO bulunamadı. Kur: pip3 install RPi.GPIO")
except KeyboardInterrupt:
    print("\nDurduruldu.")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
