"""
DHT11 Sıcaklık & Nem Sensörü Testi
Çalıştır: python3 src/tests/test_dht11.py
Beklenen çıktı: her 2 saniyede sıcaklık ve nem değeri
"""
import time

try:
    import adafruit_dht
    import board
    dht = adafruit_dht.DHT11(board.D4)
    print("DHT11 başlatıldı — GPIO4\n")
    print(f"{'Deneme':<8} {'Sıcaklık':>12} {'Nem':>10} {'Durum':>10}")
    print("-" * 44)
    for i in range(10):
        try:
            temp = dht.temperature
            hum  = dht.humidity
            if temp is not None and hum is not None:
                print(f"{i+1:<8} {temp:>10.1f} °C {hum:>8.1f} %  ✓")
            else:
                print(f"{i+1:<8} {'—':>12} {'—':>10}  boş okuma")
        except RuntimeError as e:
            print(f"{i+1:<8} {'HATA':>12} {'':>10}  {e}")
        time.sleep(2)
    dht.exit()
    print("\nTest tamamlandı.")

except ImportError:
    print("adafruit_dht kütüphanesi bulunamadı.")
    print("Kur: pip3 install adafruit-circuitpython-dht")
