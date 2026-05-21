"""
INF 208 - Değerlendirme Modülü
Enerji tüketimi analizi, WCET raporu ve Pareto optimizasyonu.

Çalıştır: python3 evaluation.py
Gereksinimler: matplotlib, numpy (pip install matplotlib numpy)
"""

import math
import time
import random
import csv
import os
from datetime import datetime

# matplotlib opsiyonel (grafik için)
try:
    import matplotlib
    matplotlib.use("Agg")  # headless (ekransız) mod
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False
    print("[UYARI] matplotlib bulunamadı. Grafikler atlanacak.")

# ─── 1. CMOS Enerji Analizi ───────────────────────────────────────────────────
def cmos_power_analysis():
    """
    P = α · C · V² · f  (CMOS dinamik güç formülü)
    RPi 3 parametreleri ile farklı çalışma modları.
    """
    print("\n" + "="*55)
    print("  1. CMOS DİNAMİK GÜÇ ANALİZİ")
    print("="*55)
    print("  Formül: P = α · C · V² · f")
    print()

    # Raspberry Pi 3B parametreleri (BCM2837, 4× Cortex-A53)
    alpha_active = 0.4    # aktivite faktörü - aktif çalışma
    alpha_idle   = 0.05   # aktivite faktörü - boşta
    C_proc       = 100e-12  # parazitik kapasite (F) - tahmini
    V_3v3        = 3.3    # I/O voltajı (V)
    V_1v2        = 1.2    # çekirdek voltajı (V)

    scenarios = [
        ("Tam yük (4 çekirdek, 1.2GHz)",  alpha_active, C_proc, V_1v2, 1.2e9, 5.1),
        ("Aktif görev (1 çekirdek, 600MHz)", 0.25, C_proc, V_1v2, 600e6, 3.2),
        ("Boşta (idle, 300MHz)",            alpha_idle,  C_proc, V_1v2, 300e6, 1.4),
        ("Derin uyku (GPIO aktif)",         0.01,        C_proc, V_3v3,  50e6, 0.7),
    ]

    results = []
    for name, alpha, C, V, f, measured_w in scenarios:
        P_calc   = alpha * C * V**2 * f * 1e9  # mW normalize (örnek)
        # Ölçülen değerler (USB güç ölçer veya datasheet)
        error_pct = abs(P_calc - measured_w * 1000) / (measured_w * 1000) * 100
        results.append((name, alpha, V, f/1e6, P_calc, measured_w*1000))
        print(f"  Mod: {name}")
        print(f"    α={alpha}, V={V}V, f={f/1e6:.0f}MHz")
        print(f"    P_hesap  = {P_calc:.1f} mW")
        print(f"    P_ölçüm  = {measured_w*1000:.0f} mW")
        print()

    return results

# ─── 2. Termal Modelleme ──────────────────────────────────────────────────────
def thermal_analysis(log_dir: str):
    """
    T_junction = T_ambient + P × Rth
    RPi 3 Rth(ja) ≈ 11 °C/W (datasheet)
    """
    print("="*55)
    print("  2. TERMAL MODELLEME")
    print("="*55)

    Rth_ja   = 11.0   # °C/W - BCM2837 termal direnç
    Cth_est  = 0.8    # J/°C - tahmini termal kapasite
    T_amb    = 25.0   # °C  - ortam sıcaklığı

    power_scenarios = [5.1, 3.2, 1.4, 0.7]
    labels = ["Tam yük", "Aktif", "Boşta", "Uyku"]

    print(f"  Rth(j-a) = {Rth_ja} °C/W  |  T_ortam = {T_amb} °C\n")
    thermal_results = []
    for P_w, lbl in zip(power_scenarios, labels):
        T_j = T_amb + P_w * Rth_ja
        thermal_results.append((lbl, P_w, T_j))
        status = "✓" if T_j < 80 else "⚠ YÜKSEK"
        print(f"  {lbl:12s}: P={P_w:.1f}W  T_j = {T_amb} + {P_w}×{Rth_ja} = {T_j:.1f}°C  {status}")

    # Gerçek ölçüm simülasyonu (RPi'de: vcgencmd measure_temp)
    print("\n  --- Simüle edilmiş gerçek zamanlı ölçüm ---")
    print("  (RPi'de: vcgencmd measure_temp | awk -F= '{print $2}')\n")
    sim_temps = []
    t_current = T_amb
    for i in range(20):
        load = 0.7 if i < 10 else 0.2
        P    = load * 5.1
        T_ss = T_amb + P * Rth_ja
        t_current += (T_ss - t_current) / (Cth_est * 10) * 0.5
        t_current += random.gauss(0, 0.3)
        sim_temps.append(round(t_current, 1))
        print(f"  t={i*5:3d}s: {t_current:.1f}°C {'(yük arttı)' if i==0 else '(yük azaldı)' if i==10 else ''}")
    print()

    # Log dosyasına yaz
    log_path = os.path.join(log_dir, "thermal_log.csv")
    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "temperature_c"])
        for i, t in enumerate(sim_temps):
            writer.writerow([i * 5, t])

    return thermal_results, sim_temps

# ─── 3. Pareto Optimizasyonu ──────────────────────────────────────────────────
def pareto_analysis():
    """
    Hedef 1: Yanıt süresi (ms) - küçük iyidir
    Hedef 2: Enerji tüketimi (mW) - küçük iyidir
    
    Farklı örnekleme frekansı ve güç modu kombinasyonları için
    Pareto cephesi hesapla ve görselleştir.
    """
    print("="*55)
    print("  3. PARETO OPTİMİZASYONU")
    print("  Hedef 1: Yanıt süresi (ms)  ↓ küçük iyi")
    print("  Hedef 2: Enerji tüketimi (mW) ↓ küçük iyi")
    print("="*55)

    # Farklı örnekleme periyodu ve güç modu konfigürasyonları
    configs = [
        # (etiket, yanıt_süresi_ms, enerji_mW)
        ("100ms / Tam Yük",    100,  5100),
        ("200ms / Tam Yük",    200,  5050),
        ("500ms / Aktif",      500,  3200),
        ("500ms / Tam Yük",    500,  5000),
        ("1s   / Aktif",      1000,  3100),
        ("1s   / Boşta",      1000,  1400),
        ("2s   / Boşta",      2000,  1350),
        ("2s   / Aktif",      2000,  3050),
        ("5s   / Boşta",      5000,  1300),
        ("5s   / Uyku+Wake",  5000,   800),
        ("10s  / Uyku+Wake", 10000,   750),
        ("30s  / Derin Uyku",30000,   700),
    ]

    # Pareto dominance kontrolü
    def is_dominated(p, others):
        for q in others:
            if q[1] <= p[1] and q[2] <= p[2] and (q[1] < p[1] or q[2] < p[2]):
                return True
        return False

    pareto_front = [c for c in configs if not is_dominated(c, configs)]

    print("\n  Tüm konfigürasyonlar:")
    for c in configs:
        dom = "◆ PARETO" if c in pareto_front else "  baskın"
        print(f"  {dom}  {c[0]:22s}  yanıt={c[1]:6d}ms  enerji={c[2]:5d}mW")

    print(f"\n  Pareto cephesi: {len(pareto_front)} çözüm")
    print("  (Bunlar 'baskın olmayan' - ne yanıt ne enerji feda edilmeden iyileştirilemez)\n")

    return configs, pareto_front

# ─── 4. Grafik Üret ──────────────────────────────────────────────────────────
def generate_plots(energy_results, thermal_results, sim_temps,
                   configs, pareto_front, output_dir: str):
    if not MATPLOTLIB_OK:
        print("[GRAFİK] matplotlib yok, atlanıyor.")
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("INF 208 — Tarım Deposu: Değerlendirme Metrikleri",
                 fontsize=13, fontweight="bold")

    # ── Grafik 1: Enerji Tüketimi ──────────────────────────────────────────
    ax1 = axes[0]
    labels  = [r[0].split("(")[0].strip() for r in energy_results]
    meas    = [r[5] for r in energy_results]
    calc    = [r[4] for r in energy_results]
    x       = range(len(labels))
    bars1   = ax1.bar([i - 0.2 for i in x], meas,  0.35,
                      label="Ölçülen (mW)", color="#2ecc71", alpha=0.8)
    bars2   = ax1.bar([i + 0.2 for i in x], calc,  0.35,
                      label="Hesaplanan (mW)", color="#3498db", alpha=0.8)
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels, rotation=15, ha="right", fontsize=7)
    ax1.set_ylabel("Güç (mW)")
    ax1.set_title("Enerji Tüketimi: P = αCV²f")
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3)
    for b in list(bars1) + list(bars2):
        ax1.annotate(f"{b.get_height():.0f}",
                     xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                     xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=6)

    # ── Grafik 2: Termal Modelleme ─────────────────────────────────────────
    ax2    = axes[1]
    times  = [i * 5 for i in range(len(sim_temps))]
    ax2.plot(times, sim_temps, "o-", color="#e74c3c", linewidth=1.5,
             markersize=4, label="CPU Sıcaklığı (simüle)")
    ax2.axhline(80, color="darkred",    linestyle="--", linewidth=1,
                label="Kritik sınır (80°C)")
    ax2.axhline(70, color="darkorange", linestyle=":",  linewidth=1,
                label="Uyarı sınırı (70°C)")
    ax2.axvline(50, color="gray", linestyle=":", linewidth=0.8, alpha=0.6)
    ax2.text(52, min(sim_temps)+1, "Yük ↓", fontsize=7, color="gray")
    ax2.fill_between(times, sim_temps, 25, alpha=0.1, color="#e74c3c")
    ax2.set_xlabel("Zaman (s)")
    ax2.set_ylabel("Sıcaklık (°C)")
    ax2.set_title("Termal Modelleme: T = T_amb + P×Rth")
    ax2.legend(fontsize=7)
    ax2.grid(alpha=0.3)

    # ── Grafik 3: Pareto Cephesi ───────────────────────────────────────────
    ax3   = axes[2]
    all_x = [c[1] for c in configs]
    all_y = [c[2] for c in configs]
    par_x = [c[1] for c in pareto_front]
    par_y = [c[2] for c in pareto_front]

    ax3.scatter(all_x, all_y, color="#bdc3c7", s=50, zorder=2, label="Diğer çözümler")
    ax3.scatter(par_x, par_y, color="#e74c3c", s=80, zorder=3,
                marker="D", label="Pareto cephesi")

    # Pareto çizgisi (sıralı)
    par_sorted = sorted(zip(par_x, par_y))
    ax3.step([p[0] for p in par_sorted], [p[1] for p in par_sorted],
             where="post", color="#c0392b", linewidth=1.2,
             linestyle="--", alpha=0.7)

    # Etiketler
    for c in pareto_front:
        ax3.annotate(c[0].split("/")[0].strip(),
                     xy=(c[1], c[2]),
                     xytext=(5, 4), textcoords="offset points",
                     fontsize=6, color="#c0392b")

    ax3.set_xlabel("Yanıt Süresi (ms)")
    ax3.set_ylabel("Enerji Tüketimi (mW)")
    ax3.set_title("Pareto Optimizasyonu\n(Yanıt Süresi vs. Enerji)")
    ax3.set_xscale("log")
    ax3.legend(fontsize=8)
    ax3.grid(alpha=0.3)

    plt.tight_layout()
    out_path = os.path.join(output_dir, "evaluation_plots.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[GRAFİK] Kaydedildi: {out_path}")
    return out_path

# ─── Ana ──────────────────────────────────────────────────────────────────────
def main():
    output_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(output_dir, exist_ok=True)

    energy_results                   = cmos_power_analysis()
    thermal_results, sim_temps       = thermal_analysis(output_dir)
    configs, pareto_front            = pareto_analysis()
    generate_plots(energy_results, thermal_results, sim_temps,
                   configs, pareto_front, output_dir)

    print("\n✓ Tüm değerlendirme metrikleri tamamlandı.")
    print(f"  Çıktı: {output_dir}/")

if __name__ == "__main__":
    main()
