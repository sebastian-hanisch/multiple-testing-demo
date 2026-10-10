"""Messreihe vor dem Text: Mehrfachtests und Gewinnerfluch auf dem Vehikel (Stück 5)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mtc_constants as C  # noqa: E402
import mtc_evaluation as E  # noqa: E402

pools = E.load_pools()
print("m = 20 Vergleiche, n = 30 Fenster je Arm; je Zeile: FWER / FDR / Teststaerke je Verfahren (R = 3000)")
for z, m1, shared in ((1.4, 0, True), (1.4, 0, False), (1.4, 2, True), (1.4, 2, False), (1.4, 5, False), (1.2, 5, False),
                      (1.2, 10, False)):
    s = E.summarize(pools, 20, m1, z, 30, reps=3000, shared=shared)
    print(f"z={z} m1={m1:2d} {'gemeinsam' if shared else 'eigene  '} (wahr {100*s['truth']:+.2f}):")
    for name in C.METHODS:
        r = s["rows"][name]
        print(f"    {C.METHOD_LABELS[name]:20s} FWER {100*r['fwer']:5.1f} %  FDR {100*r['fdr']:5.1f} %  Teststaerke {100*r['power']:5.1f} %"
              f"  Fehlalarme im Mittel {r['mean_false']:.2f}")
print("\nGewinnerfluch: alle k Varianten haben dieselbe wahre Wirkung; die beste wird gekuert (n=30, R=4000)")
for z in (1.0, 1.1, 1.2, 1.4):
    for k in (1, 3, 10, 30, 50):
        w = E.winner(pools, k, z, 30, reps=4000)
        print(f"  z={z} k={k:2d}: wahr {100*w['truth']:+.2f}  Gewinner {100*w['mean_winner']:+.2f}  sig. {100*w['winner_sig']:5.1f} %  "
              f"Bonf. {100*w['winner_bonferroni']:5.1f} %  bestaetigt {100*w['confirmed']:5.1f} %  Wiederholung {100*w['mean_replication']:+.2f}")
