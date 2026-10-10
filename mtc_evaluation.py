"""Auswertung: viele Vergleiche gleichzeitig, vier Korrekturverfahren, und die beste von k Varianten (Gewinnerfluch).

Wie in den Vorgängerstücken sind die Pools (je 10 000 simulierte Standort-Fenster je Sicherheitsfaktor, SplitMix64) die Wahrheit;
Experimente ziehen mit Zurücklegen. Neu: m Varianten von Regel B gegen Regel A, davon m1 mit echter Wirkung (Sicherheitsfaktor z), der
Rest ohne Wirkung (Sicherheitsfaktor 1,0). Kontrolle gemeinsam (ein Arm A für alle Vergleiche) oder je Vergleich eigen."""

import json
from pathlib import Path

import numpy as np
from scipy.special import stdtr

import mtc_constants as C
import mtc_multiple as M
from mtc_rng import uniform_block

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_pools.json"


def load_pools(path=PRECOMPUTED):
    """{z: Array der Fenster-Servicegrade}; z auf eine Nachkommastelle gerundet."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): np.asarray(v, dtype=float) for k, v in data["pools"].items()}


def nearest_z(z):
    return min(C.Z_GRID, key=lambda g: abs(g - z))


def true_effect(pools, z_b):
    """Wahre Wirkung von Regel B gegenüber A (Mittel der Pools, B minus A)."""
    return float(pools[nearest_z(z_b)].mean() - pools[nearest_z(C.Z_A)].mean())


def _indices(pool_size, count, seed):
    return np.minimum((uniform_block(seed, count) * pool_size).astype(np.int64), pool_size - 1)


def _welch(a, b):
    """Welch-Test über die letzte Achse. a, b sind auf (..., na) bzw. (..., nb) broadcastbar. Rückgabe: diff, p."""
    na, nb = a.shape[-1], b.shape[-1]
    va, vb = a.var(axis=-1, ddof=1) / na, b.var(axis=-1, ddof=1) / nb
    diff = b.mean(axis=-1) - a.mean(axis=-1)
    se = np.sqrt(va + vb)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = (va + vb) ** 2 / (va**2 / (na - 1) + vb**2 / (nb - 1))
        t = diff / se
    df = np.where(np.isfinite(df) & (df > 0), df, na + nb - 2)
    t = np.where(se > 0, t, 0.0)
    return diff, 2 * stdtr(df, -np.abs(t))


def simulate(pools, m, m1, z, n, reps, seed, shared=True):
    """`reps` Experimente mit m Vergleichen; die ersten m1 Varianten haben die wahre Wirkung von Sicherheitsfaktor z.
    Rückgabe: dict mit diff, p (Form (reps, m)) und real (bool, Form (m,))."""
    z = nearest_z(z)
    pa, pb_real, pb_null = pools[nearest_z(C.Z_A)], pools[z], pools[nearest_z(C.Z_A)]
    na_shape = (reps, 1, n) if shared else (reps, m, n)
    a = pa[_indices(len(pa), int(np.prod(na_shape)), seed).reshape(na_shape)]
    real = np.arange(m) < m1
    idx_b = _indices(len(pb_real), reps * m * n, seed + 1).reshape(reps, m, n)
    b = np.where(real[None, :, None], pb_real[idx_b], pb_null[_indices(len(pb_null), reps * m * n, seed + 2).reshape(reps, m, n)])
    a = np.broadcast_to(a, (reps, m, n))
    diff, p = _welch(a, b)
    return {"diff": diff, "p": p, "real": real}


def experiment_seed(m, m1, z, n, shared, tag=0):
    return 13_000_000 + 7_001 * m + 1_009 * m1 + 10_007 * int(round(z * 10)) + 131 * n + 5 * int(shared) + 13 * tag


def summarize(pools, m, m1, z, n, reps=C.LIVE_REPS, shared=True, tag=0, alpha=C.ALPHA):
    """Viele Experimente: familienweise Fehlerrate (mindestens ein Fehlalarm), Rate falscher Entdeckungen, Teststärke je echte
    Variante, jeweils für alle vier Verfahren."""
    r = simulate(pools, m, m1, z, n, reps, experiment_seed(m, m1, z, n, shared, tag), shared)
    real = r["real"]
    rej = M.rejections(r["p"], alpha)
    out = {"m": m, "m1": m1, "z": nearest_z(z), "n": n, "reps": reps, "shared": shared, "truth": true_effect(pools, z), "rows": {}}
    for name, h in rej.items():
        false_rej = h[:, ~real]
        true_rej = h[:, real]
        n_rej = h.sum(axis=1)
        out["rows"][name] = {
            "fwer": float(false_rej.any(axis=1).mean()) if (~real).any() else float("nan"),
            "fdr": float(np.where(n_rej > 0, false_rej.sum(axis=1) / np.maximum(n_rej, 1), 0.0).mean()),
            "power": float(true_rej.mean()) if real.any() else float("nan"),
            "mean_false": float(false_rej.sum(axis=1).mean()) if (~real).any() else 0.0,
            "mean_rejected": float(n_rej.mean()),
        }
    out["p"] = r["p"]
    out["real"] = real
    out["rejections"] = rej
    return out


def run_one(pools, settings):
    """Das eine Experiment der Seitenleiste: ein Lauf mit m Vergleichen."""
    r = simulate(pools, settings["m"], settings["m1"], settings["z"], settings["n"], 1, 1_000_003 * (settings["seed"] + 1) + 5,
                 settings["shared"])
    p, diff = r["p"][0], r["diff"][0]
    return {"p": p, "diff": diff, "real": r["real"], "rejections": M.rejections(p),
            "adjusted": {k: fn(p) for k, fn in M.METHODS.items()}}


def winner(pools, k, z, n, reps=C.LIVE_REPS, tag=0):
    """Die beste von k Varianten (größte geschätzte Verbesserung), alle k mit derselben wahren Wirkung (Sicherheitsfaktor z).
    Ein Wiederholungsexperiment zieht für die gekürte Variante frische n Fenster je Arm.
    Rückgabe: Mittel der Gewinner-Schätzung, wahre Wirkung, Anteil signifikant (p < 0,05 und Bonferroni), Anteil bestätigt."""
    z = nearest_z(z)
    seed = 17_000_000 + 4_001 * k + 10_007 * int(round(z * 10)) + 131 * n + 13 * tag
    pa, pb = pools[nearest_z(C.Z_A)], pools[z]
    a = pa[_indices(len(pa), reps * n, seed).reshape(reps, 1, n)]
    b = pb[_indices(len(pb), reps * k * n, seed + 1).reshape(reps, k, n)]
    diff, p = _welch(np.broadcast_to(a, (reps, k, n)), b)
    best = diff.argmax(axis=1)
    rows = np.arange(reps)
    w_diff, w_p = diff[rows, best], p[rows, best]
    a2 = pa[_indices(len(pa), reps * n, seed + 2).reshape(reps, n)]
    b2 = pb[_indices(len(pb), reps * n, seed + 3).reshape(reps, n)]
    d2, p2 = _welch(a2, b2)
    truth = true_effect(pools, z)
    return {"k": k, "z": z, "n": n, "reps": reps, "truth": truth, "mean_winner": float(w_diff.mean()),
            "winner_sig": float((w_p < C.ALPHA).mean()), "winner_bonferroni": float((w_p * k < C.ALPHA).mean()),
            "confirmed": float(((p2 < C.ALPHA) & (d2 > 0)).mean()), "winner_diffs": w_diff,
            "mean_replication": float(d2.mean())}
