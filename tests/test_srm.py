"""Zuteilungstest, Verlustmechanismen, Simulation: Handrechnung an Mini-Instanzen und Eigenschaften."""

import numpy as np
import pytest

import srm_constants as C
import srm_evaluation as E
import srm_stats as S


def test_srm_chi_square_by_hand():
    # 60 gegen 40: chi2 = (60-50)^2/50 + (40-50)^2/50 = 4,0; p = P(chi2_1 > 4) = 0,0455
    chi2, p = S.srm_test(60, 40)
    assert float(chi2) == pytest.approx(4.0)
    assert float(p) == pytest.approx(0.0455, abs=1e-4)
    chi2, p = S.srm_test(50, 50)
    assert float(chi2) == 0.0 and float(p) == pytest.approx(1.0)


def test_srm_with_no_units_is_not_an_alarm():
    chi2, p = S.srm_test(0, 0)
    assert float(chi2) == 0.0 and float(p) == pytest.approx(1.0)


def test_srm_with_a_non_even_planned_share():
    # geplant 1 : 3 (Anteil A 0,25), ausgewertet 25 : 75 bei n = 100: perfekt, chi2 = 0
    chi2, _p = S.srm_test(25, 75, share_a=0.25)
    assert float(chi2) == pytest.approx(0.0)


def test_welch_from_moments_equals_welch_on_raw_data():
    rng = np.random.default_rng(1)
    a, b = rng.normal(0, 1, 17), rng.normal(0.5, 2, 23)
    raw = S.welch(a, b)
    mom = S.welch_from_moments(len(a), a.mean(), a.var(ddof=1), len(b), b.mean(), b.var(ddof=1))
    for key in ("diff", "se", "df", "t", "p", "lo", "hi"):
        assert float(mom[key]) == pytest.approx(raw[key], rel=1e-9, abs=1e-12)


def test_welch_from_moments_needs_two_units_per_arm():
    r = S.welch_from_moments(1, 0.9, 0.0, 10, 0.95, 0.001)
    assert float(r["p"]) == 1.0 and np.isnan(float(r["diff"]))


def test_loss_masks_on_a_mini_instance():
    pool_a = np.arange(1, 101) / 100.0            # Quantile von A: f-Quantil bei f = 0,1 ist 0,109
    pool_b = pool_a + 0.1
    to_b = np.array([[False, True, True, False]])
    values = np.array([[0.05, 0.15, 0.50, 0.30]])
    u = np.array([[0.0, 0.05, 0.5, 0.01]])
    f = 0.1
    q_a, q_b = np.quantile(pool_a, f), np.quantile(pool_b, f)       # 0,109 und 0,209
    zf = E.loss_mask("zufaellig", f, to_b, values, u, pool_a, pool_b)
    assert zf.tolist() == [[False, True, False, False]]             # nur B-Fenster mit u < f
    sl = E.loss_mask("schlechteste", f, to_b, values, u, pool_a, pool_b)
    assert sl.tolist() == [[False, True, False, False]]             # B-Fenster unter q_b = 0,209
    sy = E.loss_mask("symmetrisch", f, to_b, values, u, pool_a, pool_b)
    assert sy.tolist() == [[True, True, False, False]]              # A unter 0,109 (0,05), B unter 0,209 (0,15)
    gr = E.loss_mask("grenzwert", f, to_b, values, u, pool_a, pool_b)
    assert gr.tolist() == [[True, False, False, False]]             # alle unter q_a = 0,109 (nur 0,05)
    assert q_a < q_b
    none = E.loss_mask("schlechteste", 0.0, to_b, values, u, pool_a, pool_b)
    assert not none.any()


def test_simulation_conserves_the_windows(pools):
    r = E.simulate(pools, 1.4, 200, 7, "schlechteste", 50, 99)
    assigned_a = 200 - r["assigned_b"]
    assert np.array_equal(r["n_a"] + r["lost_a"], assigned_a)
    assert np.array_equal(r["n_b"] + r["lost_b"], r["assigned_b"])
    assert np.all(r["lost_a"] == 0)                    # Mechanismus nur in B


def test_no_loss_keeps_every_window(pools):
    r = E.simulate(pools, 1.4, 120, 0, "zufaellig", 30, 5)
    assert np.all(r["lost_a"] == 0) and np.all(r["lost_b"] == 0)
    assert np.all(r["n_a"] + r["n_b"] == 120)


def test_simulation_is_deterministic(pools):
    a = E.simulate(pools, 1.4, 100, 5, "grenzwert", 20, 3)
    b = E.simulate(pools, 1.4, 100, 5, "grenzwert", 20, 3)
    assert np.array_equal(a["diff"], b["diff"], equal_nan=True)
    c = E.simulate(pools, 1.4, 100, 5, "grenzwert", 20, 4)
    assert not np.array_equal(a["diff"], c["diff"], equal_nan=True)


def test_each_mechanism_changes_the_outcome(pools):
    """Zweig-Test: jede Variante weicht von 'kein Verlust' ab (Schätzung oder Zählung)."""
    base = E.summarize(pools, 1.4, 400, 0, "zufaellig", reps=400)
    for mech in C.MECHANISMS:
        s = E.summarize(pools, 1.4, 400, 8, mech, reps=400)
        assert abs(s["mean_estimate"] - base["mean_estimate"]) > 1e-4 or s["lost_share_b"] > 0.05, mech


def test_exact_size_by_hand():
    # N = 10: chi2 > 3,84 genau bei k <= 1 oder k >= 9: 2 * (1 + 10) / 1024
    assert E.exact_size(10) == pytest.approx(22 / 1024)
    # N = 1: chi2 = 1, kein Alarm
    assert E.exact_size(1) == 0.0


def test_power_without_loss_equals_the_size():
    assert E.srm_power_by_loss(50, [0.0])[0] == pytest.approx(E.exact_size(50), abs=1e-9)


def test_power_grows_with_the_loss_and_with_the_number_of_windows():
    p = E.srm_power_by_loss(200, [0.0, 0.05, 0.1, 0.2])
    assert p == sorted(p)
    assert E.srm_power_by_loss(1000, [0.1])[0] > E.srm_power_by_loss(200, [0.1])[0]


def test_repeated_looks_inflate_the_false_alarm_rate():
    one = E.repeated_look_false_alarm(200, 1, 3000, 1)
    many = E.repeated_look_false_alarm(200, 20, 3000, 1)
    assert many > one + 0.08
    assert one == pytest.approx(E.exact_size(200), abs=0.02)
