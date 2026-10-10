"""Orakel-Tests: der Kern gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2).

1. Holm gegen geschlossenes Testen mit Bonferroni-Lokaltests (alle Teilmengen).
2. Benjamini-Hochberg gegen scipy.stats.false_discovery_control.
3. Einzel-p-Werte gegen scipy.stats.ttest_ind.
4. Gewinnerfluch gegen eine unabhängige Schleife mit numpy-Zufallszahlen (anderer Generator, andere Ziehung).
5. Familienweise Fehlerrate unabhängiger Tests gegen 1 - (1 - alpha)^m."""

import itertools

import numpy as np
import pytest
from scipy import stats

import mtc_evaluation as E
import mtc_multiple as M


def _closed_holm(p, alpha=0.05):
    m = len(p)
    out = []
    for i in range(m):
        ok = all(min(p[list(s)]) * len(s) < alpha for r in range(1, m + 1) for s in itertools.combinations(range(m), r) if i in s)
        out.append(ok)
    return np.array(out)


def test_holm_equals_closed_testing_on_random_p_values():
    rng = np.random.default_rng(21)
    for _ in range(50):
        p = rng.random(6) ** rng.uniform(1, 5)
        assert np.array_equal(M.holm(p) < 0.05, _closed_holm(p))


def test_benjamini_hochberg_equals_scipy_adjusted_p_values():
    rng = np.random.default_rng(22)
    for _ in range(30):
        p = rng.random(25) ** rng.uniform(1, 4)
        assert M.benjamini_hochberg(p) == pytest.approx(stats.false_discovery_control(p), abs=1e-12)


def test_single_comparison_p_values_equal_scipy(pools):
    r = E.simulate(pools, 6, 3, 1.4, 20, 5, 77, shared=False)
    # Rekonstruktion der Ziehung ist nicht nötig: Welch auf beliebigen Daten gegen scipy
    rng = np.random.default_rng(2)
    a, b = rng.choice(pools[1.0], (6, 20)), rng.choice(pools[1.4], (6, 20))
    _d, p = E._welch(a, b)
    for i in range(6):
        assert p[i] == pytest.approx(stats.ttest_ind(b[i], a[i], equal_var=False).pvalue, rel=1e-9)
    assert r["p"].shape == (5, 6)


def test_winner_matches_an_independent_loop(pools):
    k, n, reps = 10, 30, 3000
    rng = np.random.default_rng(31)
    pa, pb = pools[1.0], pools[1.2]
    winners = []
    for _ in range(reps):
        a = rng.choice(pa, n)
        diffs = [rng.choice(pb, n).mean() - a.mean() for _ in range(k)]
        winners.append(max(diffs))
    ref = float(np.mean(winners))
    got = E.winner(pools, k, 1.2, n, reps=4000)["mean_winner"]
    assert got == pytest.approx(ref, abs=0.0012)


def test_family_wise_error_of_independent_tests_is_one_minus_0_95_to_the_m(pools):
    for m in (5, 20):
        s = E.summarize(pools, m, 0, 1.0, 30, reps=3000, shared=False)
        assert s["rows"]["none"]["fwer"] == pytest.approx(1 - 0.95**m, abs=0.05)
