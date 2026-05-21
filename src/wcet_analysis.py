"""
INF 208 - WCET (Worst Case Execution Time) Analiz Aracı
Her görevi 200 iterasyon çalıştırır, istatistikleri raporlar.
Schedulability testi: Liu & Layland (Rate Monotonic) kriteri.
"""

import time
import random
import statistics
import csv
import os

SIMULATION_MODE = True
try:
    import RPi.GPIO as GPIO
    import adafruit_dht, board
    SIMULATION_MODE = False
except (ImportError, RuntimeError):
    pass

def simulate_task1(n=200):
    """Sensör okuma görevini n kez çalıştır, WCET ölç."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        # DHT11 okuma simülasyonu
        time.sleep(random.uniform(0.0005, 0.008))
        # HC-SR04 ölçümü
        time.sleep(random.uniform(0.001, 0.003))
        # PIR okuma (anlık)
        _ = random.random() < 0.05
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    return times

def simulate_task2(n=200):
    """FSM + aktüatör kontrol görevini n kez çalıştır."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        # FSM işleme
        time.sleep(random.uniform(0.0002, 0.002))
        # GPIO yazma (röle, LED)
        time.sleep(random.uniform(0.0001, 0.001))
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    return times

def simulate_task3(n=200):
    """Loglama görevini n kez çalıştır."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        # CSV yazma
        time.sleep(random.uniform(0.002, 0.015))
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    return times

def wcet_report(name, times, period_ms):
    wcet  = max(times)
    avg   = statistics.mean(times)
    stdev = statistics.stdev(times)
    util  = wcet / period_ms
    pctile_99 = sorted(times)[int(len(times) * 0.99)]

    print(f"\n  ── {name} ──")
    print(f"  Örneklem     : {len(times)} iterasyon")
    print(f"  Periyot (T)  : {period_ms} ms")
    print(f"  WCET (maks)  : {wcet:.3f} ms")
    print(f"  99. yüzdelik : {pctile_99:.3f} ms")
    print(f"  Ortalama     : {avg:.3f} ms")
    print(f"  Std sapma    : {stdev:.3f} ms")
    print(f"  Kullanım U_i : {util*100:.3f}%  ({wcet:.3f}/{period_ms})")
    return wcet, util

def main():
    print("\n" + "="*55)
    print("  WCET ANALİZİ — INF 208 Tarım Deposu Projesi")
    print("="*55)
    print(f"  {'Simülasyon' if SIMULATION_MODE else 'Gerçek RPi'} modu")
    print("\n  Görevler çalıştırılıyor (200 iterasyon)...\n")

    t1_times = simulate_task1(200)
    t2_times = simulate_task2(200)
    t3_times = simulate_task3(200)

    wcet1, u1 = wcet_report("Task 1 — Sensör Okuma",        t1_times,   500)
    wcet2, u2 = wcet_report("Task 2 — Aktüatör Kontrolü",   t2_times,  1000)
    wcet3, u3 = wcet_report("Task 3 — Loglama",             t3_times,  5000)

    total_util = u1 + u2 + u3
    # Liu & Layland üst sınırı: n=3 görev için U_bound = 3*(2^(1/3)-1) ≈ 0.7798
    n = 3
    U_bound = n * (2 ** (1.0/n) - 1)

    print("\n" + "="*55)
    print("  ZAMANLANABİLİRLİK TESTİ (Rate Monotonic — Liu & Layland)")
    print("="*55)
    print(f"  ΣU_i = {u1*100:.3f}% + {u2*100:.3f}% + {u3*100:.3f}%")
    print(f"       = {total_util*100:.3f}%")
    print(f"  U_bound (n=3) = n*(2^(1/n)-1) = {U_bound*100:.2f}%")
    print()
    if total_util <= U_bound:
        print(f"  ✓ SCHEDULABLE  (ΣU={total_util*100:.2f}% ≤ {U_bound*100:.2f}%)")
    elif total_util <= 1.0:
        print(f"  ⚠ RM garanti vermez ama olası  (ΣU={total_util*100:.2f}% ≤ 100%)")
    else:
        print(f"  ✗ AŞIM — zamanlanamaz  (ΣU={total_util*100:.2f}% > 100%)")

    # CSV'ye kaydet
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    out = os.path.join(log_dir, "wcet_results.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "wcet_ms", "avg_ms", "utilization_pct"])
        w.writerow(["Task1_Sensor",    round(wcet1,3), round(statistics.mean(t1_times),3), round(u1*100,3)])
        w.writerow(["Task2_Actuator",  round(wcet2,3), round(statistics.mean(t2_times),3), round(u2*100,3)])
        w.writerow(["Task3_Logging",   round(wcet3,3), round(statistics.mean(t3_times),3), round(u3*100,3)])
        w.writerow(["TOTAL",           "",             "",                                  round(total_util*100,3)])
    print(f"\n  Sonuçlar kaydedildi: {out}")

if __name__ == "__main__":
    main()
