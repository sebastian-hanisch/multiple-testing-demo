"""Mehrfachtest-Korrekturen: Bonferroni, Holm (familienweise Fehlerrate) und Benjamini-Hochberg (Rate falscher Entdeckungen).

Alle Funktionen arbeiten über die letzte Achse eines Arrays von p-Werten (Form (..., m)) und liefern angepasste p-Werte; ein
Vergleich mit alpha entscheidet. Reine Funktionen ohne Zustand."""

import numpy as np


def bonferroni(p):
    """Angepasste p-Werte p_i * m (auf 1 begrenzt)."""
    p = np.asarray(p, dtype=float)
    return np.minimum(p * p.shape[-1], 1.0)


def holm(p):
    """Holm (1979): sortiere aufsteigend, p_(i) * (m - i + 1), laufendes Maximum, auf 1 begrenzt."""
    p = np.asarray(p, dtype=float)
    m = p.shape[-1]
    order = np.argsort(p, axis=-1)
    sorted_p = np.take_along_axis(p, order, axis=-1)
    adj = sorted_p * (m - np.arange(m))
    adj = np.minimum(np.maximum.accumulate(adj, axis=-1), 1.0)
    out = np.empty_like(adj)
    np.put_along_axis(out, order, adj, axis=-1)
    return out


def benjamini_hochberg(p):
    """Benjamini und Hochberg (1995): p_(i) * m / i, laufendes Minimum von hinten, auf 1 begrenzt (gilt für unabhängige
    oder positiv abhängige Statistiken)."""
    p = np.asarray(p, dtype=float)
    m = p.shape[-1]
    order = np.argsort(p, axis=-1)
    sorted_p = np.take_along_axis(p, order, axis=-1)
    adj = sorted_p * m / (np.arange(m) + 1)
    adj = np.minimum(np.minimum.accumulate(adj[..., ::-1], axis=-1)[..., ::-1], 1.0)
    out = np.empty_like(adj)
    np.put_along_axis(out, order, adj, axis=-1)
    return out


METHODS = {"none": lambda p: np.asarray(p, dtype=float), "bonferroni": bonferroni, "holm": holm, "bh": benjamini_hochberg}
METHOD_LABELS = {"none": "Ohne Korrektur", "bonferroni": "Bonferroni", "holm": "Holm", "bh": "Benjamini-Hochberg"}


def rejections(p, alpha=0.05):
    """Ablehnungen je Methode: {Methode: bool-Array wie p}."""
    return {name: fn(p) < alpha for name, fn in METHODS.items()}
