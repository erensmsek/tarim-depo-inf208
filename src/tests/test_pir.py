"""
PIR Hareket Sensörü Testi
Çalıştır: python3 src/tests/test_pir.py
"""
import RPi.GPIO as GPIO
import time

PIR = 17

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print(f"PIR başlatıldı — GPIO{PIR}")
    print("Hazır!\n")

    print("Sensörün önünden geç. Durdurmak için Ctrl+C\n")

    onceki = GPIO.LOW
    while True:
        simdiki = GPIO.input(PIR)
        if simdiki == GPIO.HIGH and onceki == GPIO.LOW:
            print(f"  [!] HAREKET ALGILANDI — {time.strftime('%H:%M:%S')}")
        onceki = simdiki
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
