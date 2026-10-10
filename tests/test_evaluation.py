"""Experimente mit vielen Vergleichen und der Gewinnerfluch: Aufbau, Erhaltung, Orakel, Zweig-Tests."""

import numpy as np
import pytest
from scipy import stats

import mtc_constants as C
import mtc_evaluation as E


def test_simulation_has_the_right_shapes_and_real_flags(pools):
    r = E.simulate(pools, 7, 3, 1.4, 20, 50, 5)
    assert r["diff"].shape == r["p"].shape == (50, 7)
    assert r["real"].tolist() == [True, True, True, False, False, False, False]
    assert np.all((r["p"] >= 0) & (r["p"] <= 1))


def test_welch_matches_scipy_for_a_single_comparison(pools):
    pa, pb = pools[1.0], pools[1.4]
    rng = np.random.default_rng(1)
    a, b = rng.choice(pa, (4, 25)), rng.choice(pb, (4, 25))
    diff, p = E._welch(a, b)
    for i in range(4):
        ref = stats.ttest_ind(b[i], a[i], equal_var=False)
        assert p[i] == pytest.approx(ref.pvalue, rel=1e-9)
        assert diff[i] == pytest.approx(b[i].mean() - a[i].mean())


def test_shared_control_makes_the_comparisons_dependent(pools):
    """Bei gemeinsamer Kontrolle sind die Differenzen positiv korreliert, bei eigener nicht."""
    shared = E.simulate(pools, 8, 0, 1.0, 30, 1500, 7, shared=True)["diff"]
    own = E.simulate(pools, 8, 0, 1.0, 30, 1500, 7, shared=False)["diff"]
    c_shared = np.corrcoef(shared.T)[np.triu_indices(8, 1)].mean()
    c_own = np.corrcoef(own.T)[np.triu_indices(8, 1)].mean()
    assert c_shared > 0.3
    assert abs(c_own) < 0.06


def test_uncorrected_family_wise_error_follows_one_minus_095_power_m_for_independent_tests(pools):
    s = E.summarize(pools, 20, 0, 1.0, 30, reps=2000, shared=False)
    expected = 1 - (1 - 0.05) ** 20           # 64,2 % bei exakt gleichverteilten p-Werten
    assert s["rows"]["none"]["fwer"] == pytest.approx(expected, abs=0.04)


def test_bonferroni_and_holm_hold_the_family_wise_error_rate(pools):
    for shared in (True, False):
        s = E.summarize(pools, 20, 2, 1.4, 30, reps=2000, shared=shared)
        assert s["rows"]["bonferroni"]["fwer"] <= 0.065
        assert s["rows"]["holm"]["fwer"] <= 0.065
        assert s["rows"]["holm"]["power"] >= s["rows"]["bonferroni"]["power"] - 1e-12


def test_correction_costs_power_and_bh_recovers_some(pools):
    s = E.summarize(pools, 20, 5, 1.4, 30, reps=2000, shared=False)["rows"]
    assert s["none"]["power"] > s["bonferroni"]["power"] + 0.25
    assert s["bh"]["power"] > s["holm"]["power"] + 0.05
    assert s["bh"]["fdr"] <= 0.06           # BH-Niveau 5 %, m0/m = 0,75: hier deutlich darunter


def test_no_real_effect_gives_nan_power_and_equal_fdr_and_fwer(pools):
    s = E.summarize(pools, 10, 0, 1.0, 30, reps=500)["rows"]["none"]
    assert np.isnan(s["power"])
    assert s["fdr"] == pytest.approx(s["fwer"])


def test_winner_without_effect_is_a_chance_hit(pools):
    w = E.winner(pools, 30, 1.0, 30, reps=3000)
    assert w["truth"] == 0.0
    assert w["mean_winner"] > 0.012          # über 1,2 Prozentpunkte allein durch Auswahl
    assert w["winner_sig"] > 0.15
    assert w["winner_bonferroni"] < 0.04
    assert abs(w["mean_replication"]) < 0.0015


def test_winner_with_equal_effects_is_overestimated_but_replication_is_unbiased(pools):
    w1 = E.winner(pools, 1, 1.2, 30, reps=3000)
    w10 = E.winner(pools, 10, 1.2, 30, reps=3000)
    assert w1["mean_winner"] == pytest.approx(w1["truth"], abs=0.003)
    assert w10["mean_winner"] > w10["truth"] + 0.008
    assert w10["mean_replication"] == pytest.approx(w10["truth"], abs=0.003)
    assert w10["confirmed"] == pytest.approx(w1["confirmed"], abs=0.05)      # Bestätigung hängt nicht an der Auswahl


def test_run_one_is_deterministic(pools):
    a = E.run_one(pools, {"m": 12, "m1": 2, "z": 1.4, "n": 30, "shared": True, "seed": 5})
    b = E.run_one(pools, {"m": 12, "m1": 2, "z": 1.4, "n": 30, "shared": True, "seed": 5})
    assert np.array_equal(a["p"], b["p"])
    assert set(a["rejections"]) == set(C.METHODS)
    assert a["rejections"]["none"].shape == (12,)
