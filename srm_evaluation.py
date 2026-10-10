"""Auswertung: Zuteilung per Münzwurf, Datenverlust nach vier Mechanismen, Zuteilungstest (SRM) und Effekttest nebeneinander.

Wie in den Vorgängerstücken: die Pools (je 10 000 Standort-Fenster je Sicherheitsfaktor, SplitMix64) sind die Wahrheit, ein
Experiment zieht Fenster mit Zurücklegen. Neu ist die Zuteilung: jedes Fenster geht per Münzwurf an A oder B, und nach der
Zuteilung gehen Fenster verloren (Mechanismen unten); ausgewertet wird, was übrig bleibt."""

import json
from pathlib import Path

import numpy as np

import srm_constants as C
import srm_stats as S
from srm_rng import uniform_block

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_pools.json"


def load_pools(path=PRECOMPUTED):
    """{z: Array der Fenster-Servicegrade}; z auf eine Nachkommastelle gerundet."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): np.asarray(v, dtype=float) for k, v in data["pools"].items()}


def nearest_z(z):
    return min(C.Z_GRID, key=lambda g: abs(g - z))


def true_effect(pools, z_b):
    """Wahre Wirkung von Regel B gegenüber A in der gesamten Population (Mittel der Pools, B minus A)."""
    return float(pools[nearest_z(z_b)].mean() - pools[nearest_z(C.Z_A)].mean())


def _indices(pool_size, count, seed):
    return np.minimum((uniform_block(seed, count) * pool_size).astype(np.int64), pool_size - 1)


def loss_mask(mech, f, to_b, values, u, pool_a, pool_b):
    """Welche Fenster in der Auswertung fehlen (True = fehlt). `f` Anteil in 0..1, `to_b` Zuteilung, `u` Gleichverteilte.

    zufaellig: jedes Fenster von B geht mit Wahrscheinlichkeit f unabhängig vom Ergebnis verloren.
    schlechteste: Fenster von B unter dem f-Quantil der Verteilung von B fehlen (Meldung nur bei brauchbarem Ergebnis).
    symmetrisch: in jedem Arm fehlen die Fenster unter dem f-Quantil der eigenen Verteilung (gleich viele je Arm).
    grenzwert: in beiden Armen fehlen die Fenster unter demselben Grenzwert, dem f-Quantil von A."""
    if f <= 0:
        return np.zeros_like(to_b, dtype=bool)
    q_a, q_b = float(np.quantile(pool_a, f)), float(np.quantile(pool_b, f))
    if mech == "zufaellig":
        return to_b & (u < f)
    if mech == "schlechteste":
        return to_b & (values < q_b)
    if mech == "symmetrisch":
        return np.where(to_b, values < q_b, values < q_a)
    if mech == "grenzwert":
        return values < q_a
    raise ValueError(mech)


def simulate(pools, z_b, n_total, loss_pct, mech, reps, seed):
    """`reps` Experimente mit `n_total` Fenstern (Münzwurf je Fenster), Datenverlust und beiden Tests.
    Rückgabe: dict von Arrays der Länge reps (n_a, n_b: ausgewertete Fenster je Arm; srm_p; diff, p, lo, hi) und `truth`."""
    z_b = nearest_z(z_b)
    pa, pb = pools[nearest_z(C.Z_A)], pools[z_b]
    shape = (reps, n_total)
    count = reps * n_total
    to_b = uniform_block(seed, count).reshape(shape) >= 0.5
    va = pa[_indices(len(pa), count, seed + 1).reshape(shape)]
    vb = pb[_indices(len(pb), count, seed + 2).reshape(shape)]
    values = np.where(to_b, vb, va)
    u = uniform_block(seed + 3, count).reshape(shape)
    drop = loss_mask(mech, loss_pct / 100.0, to_b, values, u, pa, pb)
    in_a, in_b = ~to_b & ~drop, to_b & ~drop
    n_a, n_b = in_a.sum(axis=1), in_b.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        mean_a = (values * in_a).sum(axis=1) / n_a
        mean_b = (values * in_b).sum(axis=1) / n_b
        var_a = (((values - mean_a[:, None]) ** 2) * in_a).sum(axis=1) / (n_a - 1)
        var_b = (((values - mean_b[:, None]) ** 2) * in_b).sum(axis=1) / (n_b - 1)
    res = S.welch_from_moments(n_a, mean_a, var_a, n_b, mean_b, var_b)
    _chi2, srm_p = S.srm_test(n_a, n_b)
    assigned_b = to_b.sum(axis=1)
    return {"n_a": n_a, "n_b": n_b, "srm_p": srm_p, "diff": res["diff"], "p": res["p"], "lo": res["lo"], "hi": res["hi"],
            "assigned_b": assigned_b, "lost_b": (to_b & drop).sum(axis=1), "lost_a": (~to_b & drop).sum(axis=1),
            "truth": true_effect(pools, z_b)}


def experiment_seed(z, n, loss, mech, tag=0):
    return 7_000_000 + 10_007 * int(round(z * 10)) + 131 * n + 17 * int(loss) + 3_001 * C.MECHANISMS.index(mech) + 13 * tag


def summarize(pools, z_b, n_total, loss_pct, mech, reps=C.LIVE_REPS, tag=0):
    """Viele Experimente bei einer Einstellung: Alarmraten beider Tests, Verzerrung der Schätzung, verlorene Fenster."""
    z_b = nearest_z(z_b)
    r = simulate(pools, z_b, n_total, loss_pct, mech, reps, experiment_seed(z_b, n_total, loss_pct, mech, tag))
    truth = r["truth"]
    est = r["diff"]
    ok = np.isfinite(est)
    sig = (r["p"] < C.ALPHA) & ok
    return {
        "z": z_b, "n": n_total, "loss": loss_pct, "mech": mech, "reps": reps, "truth": truth,
        "srm_alarm": float((r["srm_p"] < C.ALPHA).mean()),
        "srm_alarm_strict": float((r["srm_p"] < C.SRM_ALPHA_STRICT).mean()),
        "effect_reject": float(sig.mean()),
        "effect_reject_wrong": float((sig & (est * (1 if truth >= 0 else -1) < 0)).mean()),
        "mean_estimate": float(np.nanmean(est)),
        "bias": float(np.nanmean(est) - truth),
        "bias_rel": float((np.nanmean(est) - truth) / truth) if truth != 0 else float("nan"),
        "sd_estimate": float(np.nanstd(est, ddof=1)),
        "lost_share_b": float(r["lost_b"].sum() / max(r["assigned_b"].sum(), 1)),
        "lost_share_a": float(r["lost_a"].sum() / max((r["n_a"] + r["lost_a"]).sum(), 1)),
        "diffs": est, "p": r["p"], "srm_p": r["srm_p"], "n_a": r["n_a"], "n_b": r["n_b"], "lo": r["lo"], "hi": r["hi"],
    }


def run_one(pools, settings):
    """Das eine Experiment der Seitenleiste (ein Lauf von `simulate` mit eigenem Seed). settings: dict z, n, loss, mech, seed."""
    r = simulate(pools, settings["z"], settings["n"], settings["loss"], settings["mech"], 1,
                 1_000_003 * (settings["seed"] + 1) + 5)
    return {k: (v[0] if isinstance(v, np.ndarray) else v) for k, v in r.items()}


def exact_size(n_total, alpha=C.ALPHA, share_a=0.5):
    """Exakte Fehlalarmrate des Chi-Quadrat-Zuteilungstests bei Münzwurf-Zuteilung von n_total Einheiten (Aufzählung)."""
    from scipy.stats import binom
    k = np.arange(n_total + 1)
    _chi2, p = S.srm_test(k, n_total - k, share_a)
    return float((binom.pmf(k, n_total, share_a) * (p < alpha)).sum())


def srm_power_by_loss(n_total, loss_values, alpha=C.ALPHA):
    """Exakte Entdeckungswahrscheinlichkeit des Zuteilungstests, wenn zufällig der Anteil f der Fenster von B fehlt: die
    ausgewerteten Fenster von B sind dann Binomial(n_B, 1 - f) mit n_B ~ Binomial(n_total, 1/2). Aufzählung über n_B."""
    from scipy.stats import binom
    out = []
    kb = np.arange(n_total + 1)
    w = binom.pmf(kb, n_total, 0.5)
    for f in loss_values:
        # n_A = n_total - kb; n_B_kept ~ Binomial(kb, 1 - f)
        p_reject = 0.0
        for k, wk in zip(kb, w):
            if wk < 1e-12:
                continue
            j = np.arange(k + 1)
            pj = binom.pmf(j, k, 1 - f)
            _c, p = S.srm_test(np.full_like(j, n_total - k, dtype=float), j.astype(float))
            p_reject += wk * float((pj * (p < alpha)).sum())
        out.append(p_reject)
    return out


def repeated_look_false_alarm(n_total, looks, reps, seed, alpha=C.ALPHA):
    """Anteil der Experimente ohne jeden Verlust, in denen der Zuteilungstest bei mindestens einer von `looks` gleichmäßig
    verteilten Prüfungen anschlägt (die Zuteilung füllt sich nach und nach)."""
    to_b = uniform_block(seed, reps * n_total).reshape(reps, n_total) >= 0.5
    cum_b = np.cumsum(to_b, axis=1)
    positions = np.unique(np.maximum((np.arange(1, looks + 1) * n_total) // looks, 1)) - 1
    nb = cum_b[:, positions].astype(float)
    na = (positions + 1)[None, :] - nb
    _chi2, p = S.srm_test(na, nb)
    return float((p < alpha).any(axis=1).mean())
