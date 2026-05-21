"""
PIR Hareket Sensörü Testi
Çalıştır: python3 src/tests/test_pir.py
Beklenen çıktı: hareket algılandığında ekrana yazar
"""
import RPi.GPIO as GPIO
import time

PIR = 17

def hareket_algilandi(channel):
    print(f"  [!] HAREKET ALGILANDI — {time.strftime('%H:%M:%S')}")

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIR, GPIO.IN)
    GPIO.add_event_detect(PIR, GPIO.RISING,
                          callback=hareket_algilandi, bouncetime=500)

    print(f"PIR başlatıldı — GPIO{PIR}")
    print("Sensörün önünden geç, hareket algılanınca yazacak.")
    print("Durdurmak için Ctrl+C\n")

    for i in range(30):
        durum = "HAREKET VAR" if GPIO.input(PIR) else "sessiz"
        print(f"  {time.strftime('%H:%M:%S')}  {durum}", end="\r")
        time.sleep(1)

    print("\nTest tamamlandı.")
except ImportError:
    print("RPi.GPIO bulunamadı. Kur: pip3 install RPi.GPIO")
except KeyboardInterrupt:
    print("\nDurduruldu.")
finally:
    try:
        GPIO.cleanup()
    except:
        pass
