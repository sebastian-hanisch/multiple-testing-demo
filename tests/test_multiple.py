"""Korrekturverfahren: Handrechnung, Gegenprobe gegen scipy und gegen geschlossenes Testen; Eigenschaften."""

import itertools

import numpy as np
import pytest
from scipy import stats

import mtc_multiple as M


def test_bonferroni_by_hand():
    p = np.array([0.001, 0.01, 0.04, 0.20])
    assert M.bonferroni(p).tolist() == pytest.approx([0.004, 0.04, 0.16, 0.80])
    assert M.bonferroni(np.array([0.5, 0.9])).tolist() == [1.0, 1.0]       # auf 1 begrenzt


def test_holm_by_hand():
    # sortiert 0,001 < 0,01 < 0,04 < 0,20, m = 4: 0,001*4 = 0,004; 0,01*3 = 0,03; 0,04*2 = 0,08; 0,20*1 = 0,20
    p = np.array([0.04, 0.001, 0.20, 0.01])
    assert M.holm(p).tolist() == pytest.approx([0.08, 0.004, 0.20, 0.03])


def test_holm_takes_the_running_maximum():
    # 0,01*3 = 0,03 und 0,011*2 = 0,022: das Maximum bis dahin gilt (0,03)
    p = np.array([0.01, 0.011, 0.5])
    assert M.holm(p).tolist() == pytest.approx([0.03, 0.03, 0.5])


def test_benjamini_hochberg_by_hand():
    # sortiert 0,001 0,01 0,04 0,20, m = 4: p*m/i = 0,004 0,02 0,0533 0,20; laufendes Minimum von hinten
    p = np.array([0.04, 0.001, 0.20, 0.01])
    assert M.benjamini_hochberg(p).tolist() == pytest.approx([0.053333, 0.004, 0.20, 0.02], abs=1e-5)


def test_benjamini_hochberg_equals_scipy():
    rng = np.random.default_rng(3)
    for _ in range(30):
        p = rng.random(rng.integers(2, 40)) ** rng.uniform(1, 4)
        assert M.benjamini_hochberg(p) == pytest.approx(stats.false_discovery_control(p, method="bh"), abs=1e-12)


def _closed_testing_holm(p, alpha):
    """Unabhängiger Weg: geschlossenes Testen mit Bonferroni-Lokaltests über alle Teilmengen der Nullhypothesen."""
    m = len(p)
    reject = np.zeros(m, dtype=bool)
    for i in range(m):
        ok = True
        for r in range(1, m + 1):
            for subset in itertools.combinations(range(m), r):
                if i in subset and min(p[list(subset)]) * len(subset) >= alpha:
                    ok = False
                    break
            if not ok:
                break
        reject[i] = ok
    return reject


def test_holm_equals_closed_testing_with_bonferroni_local_tests():
    rng = np.random.default_rng(4)
    for _ in range(60):
        p = rng.random(7) ** rng.uniform(1, 5)
        assert np.array_equal(M.holm(p) < 0.05, _closed_testing_holm(p, 0.05))


def test_holm_never_rejects_less_than_bonferroni_and_bh_never_less_than_holm():
    rng = np.random.default_rng(5)
    for _ in range(200):
        p = rng.random(15) ** rng.uniform(1, 6)
        b, h, bh = M.bonferroni(p) < 0.05, M.holm(p) < 0.05, M.benjamini_hochberg(p) < 0.05
        assert np.all(h | ~b)          # Bonferroni-Ablehnung impliziert Holm-Ablehnung
        assert np.all(bh | ~h)         # Holm-Ablehnung impliziert BH-Ablehnung


def test_adjustments_work_row_wise_on_matrices():
    rng = np.random.default_rng(6)
    p = rng.random((5, 9))
    for fn in (M.bonferroni, M.holm, M.benjamini_hochberg):
        mat = fn(p)
        for i in range(5):
            assert mat[i].tolist() == pytest.approx(fn(p[i]).tolist())


def test_rejections_has_all_four_methods():
    r = M.rejections(np.array([0.001, 0.2]))
    assert set(r) == {"none", "bonferroni", "holm", "bh"}
    assert r["none"].tolist() == [True, False]
