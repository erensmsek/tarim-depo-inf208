"""
PIR Hareket Sensörü Testi
Çalıştır: python3 src/tests/test_pir.py
"""
import RPi.GPIO as GPIO
import time

PIR = 17

def hareket_algilandi(channel):
    print(f"  [!] HAREKET ALGILANDI — {time.strftime('%H:%M:%S')}")

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIR, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    print(f"PIR başlatıldı — GPIO{PIR}")
    print("Sensör kalibre oluyor, 30 saniye bekle...", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
    print(" hazır!\n")

    GPIO.add_event_detect(PIR, GPIO.RISING, callback=hareket_algilandi, bouncetime=500)

    print("Sensörün önünden geç. Durdurmak için Ctrl+C\n")

    while True:
        time.sleep(0.1)

except ImportError:
    print("RPi.GPIO bulunamadı. Kur: pip3 install RPi.GPIO")
except KeyboardInterrupt:
    print("\nDurduruldu.")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
