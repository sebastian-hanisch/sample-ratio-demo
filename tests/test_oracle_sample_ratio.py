"""Orakel-Tests: der Kern gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2).

1. Chi-Quadrat-Zuteilungstest gegen scipy.stats.chisquare.
2. Exakte Fehlalarmrate (Aufzählung der Binomialverteilung) gegen die Simulation des Münzwurfs.
3. Exakte Entdeckungswahrscheinlichkeit bei zufälligem Verlust gegen die vektorisierte Simulation (Mechanismus zufällig).
4. Servicegrad-Formel gegen die Simulation und Poolmittel (Vehikel der Linie)."""

import numpy as np
import pytest
from scipy import stats

import srm_constants as C
import srm_evaluation as E
import srm_formulas as F
import srm_stats as S
import srm_vehicle as V
from srm_rng import SplitMix64


def test_srm_test_equals_scipy_chisquare():
    rng = np.random.default_rng(3)
    for _ in range(40):
        na, nb = int(rng.integers(5, 400)), int(rng.integers(5, 400))
        ref = stats.chisquare([na, nb])
        chi2, p = S.srm_test(na, nb)
        assert float(chi2) == pytest.approx(ref.statistic, rel=1e-12)
        assert float(p) == pytest.approx(ref.pvalue, rel=1e-9, abs=1e-14)


def test_exact_size_matches_a_simulated_coin_flip_allocation():
    for n in (40, 100, 400):
        rng = np.random.default_rng(10 + n)
        to_b = rng.random((40000, n)) >= 0.5
        nb = to_b.sum(axis=1)
        _c, p = S.srm_test(n - nb, nb)
        assert float((p < 0.05).mean()) == pytest.approx(E.exact_size(n), abs=0.006)


def test_exact_power_matches_the_simulation_for_random_loss(pools):
    for n, loss in ((400, 10), (1000, 5)):
        sim = E.summarize(pools, 1.4, n, loss, "zufaellig", reps=3000)["srm_alarm"]
        exact = E.srm_power_by_loss(n, [loss / 100])[0]
        assert sim == pytest.approx(exact, abs=0.02), (n, loss)


def test_fill_rate_formula_against_simulation_and_pools(pools):
    rng = SplitMix64(77)
    demand = short = 0
    for _ in range(800):
        d, s = V.simulate_window(1.4, rng)
        demand += d
        short += s
    assert 1 - short / demand == pytest.approx(F.fill_rate(1.4), abs=0.005)
    assert pools[1.4].mean() == pytest.approx(F.fill_rate(1.4), abs=0.004)


def test_random_loss_does_not_bias_the_estimate(pools):
    s = E.summarize(pools, 1.4, 600, 10, "zufaellig", reps=2000)
    assert abs(s["bias"]) < 0.0006          # unter 0,06 Prozentpunkte
