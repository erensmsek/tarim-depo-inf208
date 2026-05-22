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
    GPIO.setup(PIR, GPIO.IN)

    print(f"PIR başlatıldı — GPIO{PIR}")
    print("Sensör kalibre oluyor, 30 saniye bekle...", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
    print(" hazır!\n")

    print("Sensörün önünden geç. Durdurmak için Ctrl+C\n")

    print(f"{'Deneme':<8} {'Durum':<20} {'Saat'}")
    print("-" * 44)

    for i in range(30):
        durum = GPIO.input(PIR)
        if durum == GPIO.HIGH:
            print(f"{i+1:<8} HAREKET ALGILANDI !!   {time.strftime('%H:%M:%S')}")
        else:
            print(f"{i+1:<8} sessiz               {time.strftime('%H:%M:%S')}", end="\r")
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
