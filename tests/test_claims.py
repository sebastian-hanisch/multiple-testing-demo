"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Funktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Pools und -Ziehungen); die Bänder sind Rundungs- und Plattformreserve."""

import pytest

import mtc_evaluation as E

REPS = 3000


def pct(x):
    return 100 * x


def rows(pools, m1, z, shared):
    return E.summarize(pools, 20, m1, z, 30, reps=REPS, shared=shared)["rows"]


def test_twenty_useless_variants_without_correction(pools):
    shared = rows(pools, 0, 1.4, True)
    own = rows(pools, 0, 1.4, False)
    assert pct(shared["none"]["fwer"]) == pytest.approx(40.4, abs=1.8)
    assert pct(own["none"]["fwer"]) == pytest.approx(64.3, abs=1.8)
    assert 100 * (1 - 0.95**20) == pytest.approx(64.2, abs=0.05)
    for method in ("bonferroni", "holm"):
        assert pct(shared[method]["fwer"]) == pytest.approx(3.6, abs=1.2)
        assert pct(own[method]["fwer"]) == pytest.approx(5.2, abs=1.2)
    assert pct(own["bh"]["fwer"]) == pytest.approx(5.2, abs=1.2)


def test_two_real_effects_the_price_of_correction(pools):
    shared = rows(pools, 2, 1.4, True)
    assert pct(shared["none"]["power"]) == pytest.approx(85.6, abs=1.8)
    assert pct(shared["bonferroni"]["power"]) == pytest.approx(45.1, abs=2.0)
    assert pct(shared["holm"]["power"]) == pytest.approx(45.4, abs=2.0)
    assert pct(shared["bh"]["power"]) == pytest.approx(50.5, abs=2.0)
    gap = pct(shared["holm"]["power"] - shared["bonferroni"]["power"])
    assert 0.0 <= gap <= 1.0                  # Holm gegen Bonferroni: etwa 0,3 Prozentpunkte
    assert pct(shared["bh"]["fwer"]) == pytest.approx(6.3, abs=1.5)
    assert pct(shared["none"]["fdr"]) == pytest.approx(21.2, abs=2.0)
    own = rows(pools, 2, 1.4, False)
    assert pct(own["none"]["fdr"]) == pytest.approx(28.2, abs=2.0)
    assert pct(own["bh"]["fwer"]) == pytest.approx(8.7, abs=1.8)


def test_five_real_effects_benjamini_hochberg_finds_more_but_not_for_free(pools):
    r = rows(pools, 5, 1.4, False)
    assert pct(r["holm"]["power"]) == pytest.approx(46.8, abs=2.0)
    assert pct(r["bh"]["power"]) == pytest.approx(62.9, abs=2.0)
    assert pct(r["bh"]["fwer"]) == pytest.approx(15.0, abs=2.0)
    assert pct(r["bh"]["fdr"]) == pytest.approx(3.7, abs=1.0)
    assert pct(r["none"]["fdr"]) == pytest.approx(13.4, abs=2.0)


def test_small_effects_correction_costs_almost_everything(pools):
    r = rows(pools, 5, 1.2, False)
    assert pct(r["none"]["power"]) == pytest.approx(34.6, abs=2.0)
    assert pct(r["bonferroni"]["power"]) == pytest.approx(6.3, abs=1.5)
    assert pct(r["bh"]["power"]) == pytest.approx(8.2, abs=1.5)
    assert pct(r["none"]["fdr"]) == pytest.approx(28.2, abs=2.5)


def test_winner_without_any_effect(pools):
    w10 = E.winner(pools, 10, 1.0, 30, reps=4000)
    w30 = E.winner(pools, 30, 1.0, 30, reps=4000)
    assert pct(w10["mean_winner"]) == pytest.approx(1.40, abs=0.10)
    assert pct(w10["winner_sig"]) == pytest.approx(15.1, abs=2.0)
    assert pct(w10["confirmed"]) == pytest.approx(2.3, abs=1.0)
    assert pct(w30["mean_winner"]) == pytest.approx(1.84, abs=0.10)
    assert pct(w30["winner_sig"]) == pytest.approx(26.3, abs=2.0)
    assert pct(w30["winner_bonferroni"]) == pytest.approx(1.7, abs=1.0)


def test_winner_with_equal_small_effects(pools):
    w1 = E.winner(pools, 1, 1.2, 30, reps=4000)
    w10 = E.winner(pools, 10, 1.2, 30, reps=4000)
    w50 = E.winner(pools, 50, 1.2, 30, reps=4000)
    assert pct(w10["truth"]) == pytest.approx(1.96, abs=0.06)
    assert pct(w1["mean_winner"]) == pytest.approx(1.94, abs=0.12)
    assert pct(w10["mean_winner"]) == pytest.approx(3.15, abs=0.12)
    assert pct(w50["mean_winner"]) == pytest.approx(3.62, abs=0.12)
    assert w10["mean_winner"] / w10["truth"] == pytest.approx(1.6, abs=0.08)
    assert pct(w10["winner_sig"]) == pytest.approx(81.2, abs=2.0)
    assert pct(w10["confirmed"]) == pytest.approx(35.1, abs=2.0)
    assert pct(w10["mean_replication"]) == pytest.approx(1.97, abs=0.1)


def test_winner_with_a_clear_effect_is_overestimated_less(pools):
    w = E.winner(pools, 10, 1.4, 30, reps=4000)
    assert w["mean_winner"] / w["truth"] == pytest.approx(1.28, abs=0.05)
