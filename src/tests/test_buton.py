"""
Push Buton (Reset) Testi
Çalıştır: python3 src/tests/test_buton.py
Beklenen çıktı: butona basınca ekrana yazar
"""
import RPi.GPIO as GPIO
import time

BUTON = 5

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(BUTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print(f"Buton hazır — GPIO{BUTON}")
    print("Butona bas. Durdurmak için Ctrl+C\n")

    print(f"{'Deneme':<8} {'Durum':<20} {'Saat'}")
    print("-" * 44)

    i = 0
    while True:
        if GPIO.input(BUTON) == GPIO.LOW:
            i += 1
            print(f"{i:<8} BUTONA BASILDI !!    {time.strftime('%H:%M:%S')}")
            time.sleep(0.3)  # debounce
        else:
            print(f"{'–':<8} bekleniyor           {time.strftime('%H:%M:%S')}", end="\r")
        time.sleep(0.05)

except ImportError:
    print("RPi.GPIO bulunamadı. Kur: pip3 install RPi.GPIO")
except KeyboardInterrupt:
    print("\nDurduruldu.")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
