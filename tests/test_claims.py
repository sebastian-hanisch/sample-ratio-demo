"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Funktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Pools und -Ziehungen, exakte Aufzählungen); die Bänder sind Rundungsreserve."""

import pytest

import srm_evaluation as E

REPS = 3000


def pp(x):
    return 100 * x


def test_exact_false_alarm_rate_of_the_allocation_test():
    assert pp(E.exact_size(40)) == pytest.approx(3.85, abs=0.01)
    assert pp(E.exact_size(100)) == pytest.approx(5.69, abs=0.01)
    assert pp(E.exact_size(400)) == pytest.approx(5.10, abs=0.01)
    assert pp(E.exact_size(2000)) == pytest.approx(5.17, abs=0.01)
    assert pp(E.exact_size(400, 0.001)) == pytest.approx(0.11, abs=0.01)


def test_detection_of_random_loss_in_b_by_the_allocation_test_is_low():
    p400 = dict(zip((0.05, 0.10, 0.20), E.srm_power_by_loss(400, [0.05, 0.10, 0.20])))
    assert pp(p400[0.05]) == pytest.approx(8.1, abs=0.1)
    assert pp(p400[0.10]) == pytest.approx(17.4, abs=0.1)
    assert pp(p400[0.20]) == pytest.approx(55.9, abs=0.1)
    p2000 = dict(zip((0.05, 0.10, 0.20), E.srm_power_by_loss(2000, [0.05, 0.10, 0.20])))
    assert pp(p2000[0.05]) == pytest.approx(20.5, abs=0.1)
    assert pp(p2000[0.10]) == pytest.approx(63.1, abs=0.1)
    assert pp(p2000[0.20]) == pytest.approx(99.7, abs=0.1)


def test_repeated_checks_of_the_allocation_test():
    rates = {k: pp(E.repeated_look_false_alarm(400, k, 4000, 4242)) for k in (1, 2, 5, 10, 30)}
    assert rates[1] == pytest.approx(5.1, abs=1.0)
    assert rates[2] == pytest.approx(9.0, abs=1.5)
    assert rates[5] == pytest.approx(14.4, abs=1.5)
    assert rates[10] == pytest.approx(19.2, abs=1.5)
    assert rates[30] == pytest.approx(28.2, abs=1.5)


def test_without_effect_the_worst_windows_missing_in_b_create_a_false_effect(pools):
    s2 = E.summarize(pools, 1.0, 400, 2, "schlechteste", reps=REPS)
    assert pp(s2["effect_reject"]) == pytest.approx(10.0, abs=1.2)
    assert pp(s2["srm_alarm"]) == pytest.approx(5.8, abs=1.0)
    assert pp(s2["bias"]) == pytest.approx(0.33, abs=0.06)
    s5 = E.summarize(pools, 1.0, 400, 5, "schlechteste", reps=REPS)
    assert pp(s5["effect_reject"]) == pytest.approx(26.8, abs=1.5)
    assert pp(s5["srm_alarm"]) == pytest.approx(7.2, abs=1.0)
    assert pp(s5["bias"]) == pytest.approx(0.66, abs=0.06)
    big = E.summarize(pools, 1.0, 2000, 5, "schlechteste", reps=REPS)
    assert pp(big["effect_reject"]) == pytest.approx(87.2, abs=2.0)
    assert pp(big["srm_alarm"]) == pytest.approx(20.6, abs=1.5)


def test_random_loss_is_harmless_for_the_estimate(pools):
    s = E.summarize(pools, 1.0, 400, 5, "zufaellig", reps=REPS)
    assert abs(pp(s["bias"])) < 0.06
    assert pp(s["effect_reject"]) == pytest.approx(4.1, abs=1.2)


def test_with_a_real_effect_the_three_distorting_mechanisms(pools):
    truth = 100 * E.true_effect(pools, 1.4)
    assert truth == pytest.approx(3.49, abs=0.06)
    worst = E.summarize(pools, 1.4, 400, 5, "schlechteste", reps=REPS)
    assert pp(worst["bias"]) == pytest.approx(0.52, abs=0.07)
    assert worst["bias_rel"] == pytest.approx(0.15, abs=0.02)
    sym = E.summarize(pools, 1.4, 400, 5, "symmetrisch", reps=REPS)
    assert pp(sym["bias"]) == pytest.approx(-0.13, abs=0.07)
    assert pp(sym["srm_alarm"]) == pytest.approx(5.0, abs=1.2)
    lim = E.summarize(pools, 1.4, 400, 5, "grenzwert", reps=REPS)
    assert pp(lim["bias"]) == pytest.approx(-0.56, abs=0.07)
    assert lim["bias_rel"] == pytest.approx(-0.16, abs=0.02)
    assert pp(lim["lost_share_b"]) == pytest.approx(0.6, abs=0.2)
    assert pp(lim["lost_share_a"]) == pytest.approx(5.1, abs=0.3)
    big = E.summarize(pools, 1.4, 2000, 5, "grenzwert", reps=REPS)
    assert pp(big["srm_alarm"]) == pytest.approx(16.4, abs=1.5)
