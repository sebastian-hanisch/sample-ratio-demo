"""Zwei-Gruppen-Vergleich: Welch-Test mit Konfidenzintervall (skalar und vektorisiert), Normalformel für den Umfang."""

import math

import numpy as np
from scipy.special import ndtri, stdtr, stdtrit


def welch(a, b, conf=0.95):
    """Welch-t-Test für die Differenz mean(b) - mean(a). Rückgabe: dict(diff, se, df, t, p, lo, hi)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    va, vb = a.var(ddof=1) / na, b.var(ddof=1) / nb
    diff = float(b.mean() - a.mean())
    se = math.sqrt(va + vb)
    if se == 0:
        return {"diff": diff, "se": 0.0, "df": float(na + nb - 2), "t": 0.0 if diff == 0 else math.inf,
                "p": 1.0 if diff == 0 else 0.0, "lo": diff, "hi": diff}
    df = (va + vb) ** 2 / (va**2 / (na - 1) + vb**2 / (nb - 1))
    t = diff / se
    p = float(2 * stdtr(df, -abs(t)))
    q = float(stdtrit(df, 0.5 + conf / 2))
    return {"diff": diff, "se": se, "df": df, "t": t, "p": p, "lo": diff - q * se, "hi": diff + q * se}


def welch_batch(a, b, conf=0.95):
    """Dasselbe für viele Experimente zugleich: a Form (R, na), b Form (R, nb). Rückgabe: dict von Arrays der Länge R."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = a.shape[1], b.shape[1]
    va, vb = a.var(axis=1, ddof=1) / na, b.var(axis=1, ddof=1) / nb
    diff = b.mean(axis=1) - a.mean(axis=1)
    se = np.sqrt(va + vb)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = (va + vb) ** 2 / (va**2 / (na - 1) + vb**2 / (nb - 1))
        t = diff / se
    df = np.where(np.isfinite(df), df, na + nb - 2)
    t = np.where(se > 0, t, 0.0)
    p = 2 * stdtr(df, -np.abs(t))
    q = stdtrit(df, 0.5 + conf / 2)
    return {"diff": diff, "se": se, "df": df, "t": t, "p": p, "lo": diff - q * se, "hi": diff + q * se}


def n_per_arm_normal(delta, sd_a, sd_b, alpha=0.05, power=0.8):
    """Normalformel für die Einheiten je Arm: (z_{1-alpha/2} + z_power)^2 (sd_a^2 + sd_b^2) / delta^2 (aufgerundet)."""
    if delta == 0:
        return math.inf
    z = ndtri(1 - alpha / 2) + ndtri(power)
    return int(math.ceil(z**2 * (sd_a**2 + sd_b**2) / delta**2))


def srm_test(n_a, n_b, share_a=0.5):
    """Chi-Quadrat-Test auf das Zuteilungsverhältnis (Sample-Ratio-Mismatch) für die ausgewerteten Zahlen n_a, n_b (Arrays
    oder Zahlen). Rückgabe: (chi², p). Ohne Einheiten (n_a + n_b = 0) ist p = 1."""
    from scipy.special import chdtrc
    n_a = np.asarray(n_a, dtype=float)
    n_b = np.asarray(n_b, dtype=float)
    n = n_a + n_b
    e_a, e_b = n * share_a, n * (1 - share_a)
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.where(n > 0, (n_a - e_a) ** 2 / e_a + (n_b - e_b) ** 2 / e_b, 0.0)
    return chi2, chdtrc(1, chi2)


def welch_from_moments(n_a, mean_a, var_a, n_b, mean_b, var_b, conf=0.95):
    """Welch-Test aus Zahlen, Mittelwerten und Varianzen (Arrays; Varianz mit ddof = 1). Arme mit weniger als zwei Einheiten
    liefern p = 1 und eine Differenz von NaN."""
    n_a = np.asarray(n_a, dtype=float)
    n_b = np.asarray(n_b, dtype=float)
    ok = (n_a >= 2) & (n_b >= 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        va, vb = var_a / n_a, var_b / n_b
        diff = mean_b - mean_a
        se = np.sqrt(va + vb)
        df = (va + vb) ** 2 / (va**2 / (n_a - 1) + vb**2 / (n_b - 1))
        t = diff / se
    df = np.where(np.isfinite(df), df, 1.0)
    t = np.where(np.isfinite(t), t, 0.0)
    p = np.where(ok, 2 * stdtr(df, -np.abs(t)), 1.0)
    q = stdtrit(df, 0.5 + conf / 2)
    return {"diff": np.where(ok, diff, np.nan), "se": se, "df": df, "t": t, "p": p,
            "lo": np.where(ok, diff - q * se, np.nan), "hi": np.where(ok, diff + q * se, np.nan)}
