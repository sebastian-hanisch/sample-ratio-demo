"""Messreihe vor dem Text: Zuteilungstest (SRM) und Effekttest bei Datenverlust nach vier Mechanismen (Stück 3)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

import srm_constants as C  # noqa: E402
import srm_evaluation as E  # noqa: E402

pools = E.load_pools()
print("Exakte Fehlalarmrate des SRM-Tests bei Münzwurf (alpha 0,05 / 0,001):")
for n in (40, 100, 400, 2000):
    print(f"  N={n}: {100*E.exact_size(n):.2f} % / {100*E.exact_size(n, 0.001):.3f} %")
print("Wiederholtes Prüfen (ohne Verlust), N=400:")
for k in (1, 2, 5, 10, 30):
    print(f"  {k:2d} Prüfungen: {100*E.repeated_look_false_alarm(400, k, 6000, 77):.1f} %")
print("\nEntdeckung durch SRM bei ZUFÄLLIGEM Verlust nur in B (exakt, alpha 0,05 / 0,001):")
for n in (100, 400, 2000):
    f = [0.01, 0.02, 0.05, 0.10, 0.20]
    print(f"  N={n}: " + "  ".join(f"{int(100*x)}%:{100*p:.1f}/{100*q:.1f}"
          for x, p, q in zip(f, E.srm_power_by_loss(n, f), E.srm_power_by_loss(n, f, 0.001))))
print("\nMechanismen (R=3000): Verlust-% ist der Soll-Anteil in B")
hdr = "mech          z   N    f%  | SRM .05 / .001 | Effekt sig. | Schätzung (wahr) Verzerrung   | verlor B/A"
print(hdr)
for z in (1.0, 1.4):
    for n in (100, 400, 2000):
        for mech in C.MECHANISMS:
            for f in (2, 5):
                s = E.summarize(pools, z, n, f, mech, reps=3000)
                print(f"{mech:12s} {z:.1f} {n:5d} {f:3d}  | {100*s['srm_alarm']:5.1f} / {100*s['srm_alarm_strict']:5.1f}"
                      f" | {100*s['effect_reject']:5.1f} % | {100*s['mean_estimate']:+.2f} ({100*s['truth']:+.2f})"
                      f" {100*s['bias']:+.2f} | {100*s['lost_share_b']:.1f}/{100*s['lost_share_a']:.1f}")
