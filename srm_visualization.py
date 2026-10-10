"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import srm_constants as C

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=330, legend=dict(orientation="h", y=-0.22))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_counts(assigned_a, assigned_b, kept_a, kept_b):
    """Zugeteilte und ausgewertete Fenster je Arm (Säulen nebeneinander)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Regel A", "Regel B"], y=[assigned_a, assigned_b], name="zugeteilt", marker_color=C.COLOR_OK))
    fig.add_trace(go.Bar(x=["Regel A", "Regel B"], y=[kept_a, kept_b], name="ausgewertet", marker_color=[C.COLOR_A, C.COLOR_B]))
    fig.update_layout(barmode="group")
    return _finish(fig, "Fenster je Arm", None, "Fenster", height=300)


def build_interval(est, lo, hi, truth):
    """Geschätzte Differenz mit 95-%-Intervall; senkrecht: Null und die wahre Wirkung, in Prozentpunkten."""
    fig = go.Figure()
    if np.isfinite(est):
        fig.add_trace(go.Scatter(x=[100 * est], y=[0], mode="markers", name="Schätzung",
                                 error_x=dict(type="data", symmetric=False, array=[100 * (hi - est)],
                                              arrayminus=[100 * (est - lo)], thickness=3, width=10, color=C.COLOR_B),
                                 marker=dict(color=C.COLOR_B, size=14)))
    fig.add_vline(x=0, line=dict(color="gray", width=1.5), annotation_text="kein Unterschied", annotation_position="top")
    fig.add_vline(x=100 * truth, line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"), annotation_text="wahre Wirkung",
                  annotation_position="bottom")
    fig.update_yaxes(visible=False, range=[-1, 1])
    return _finish(fig, "Differenz B minus A mit 95-%-Intervall", "Prozentpunkte Servicegrad", None, height=210)


def build_histogram(diffs, sig, truth):
    """Geschätzte Differenz in vielen Wiederholungen; signifikante und nicht signifikante getrennt eingefärbt."""
    d = 100 * np.asarray(diffs, dtype=float)
    ok = np.isfinite(d)
    d, sig = d[ok], np.asarray(sig)[ok]
    lo, hi = float(min(d.min(), 0, 100 * truth)), float(max(d.max(), 0, 100 * truth))
    size = max((hi - lo) / 40, 1e-9)
    fig = go.Figure()
    for mask, name, color in ((~sig, "nicht signifikant", C.COLOR_OK), (sig, "signifikant (p unter 0,05)", C.COLOR_B)):
        if mask.any():
            fig.add_trace(go.Histogram(x=d[mask], name=name, marker_color=color, xbins=dict(start=lo, end=hi + size, size=size)))
    fig.update_layout(barmode="stack")
    fig.add_vline(x=0, line=dict(color="gray", width=1.5), annotation_text="kein Unterschied", annotation_position="top left")
    fig.add_vline(x=100 * truth, line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"), annotation_text="wahre Wirkung",
                  annotation_position="top right")
    return _finish(fig, "Geschätzte Differenz in vielen Wiederholungen", "Prozentpunkte Servicegrad (B minus A)", "Experimente")


def build_srm_power(curves, n_now, loss_now):
    """Wie oft der Zuteilungstest einen zufälligen Verlust in B bemerkt: Kurve je Fenster-Zahl. curves: {n: [(loss, p), ...]}."""
    palette = ["#4c78a8", "#2F6B65", "#d95f02", "#7570b3"]
    fig = go.Figure()
    for i, (n, pts) in enumerate(sorted(curves.items())):
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[100 * p[1] for p in pts], mode="lines+markers",
                                 name=f"{C.fmt_int(n)} Fenster", line=dict(color=palette[i % len(palette)], width=3 if n == n_now else 2)))
    fig.add_hline(y=80, line=dict(color="gray", dash="dot"), annotation_text="80 %", annotation_position="bottom right")
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="5 % (Fehlalarm)", annotation_position="top right")
    fig.update_yaxes(range=[0, 102])
    return _finish(fig, "Anteil der Experimente, in denen der Zuteilungstest anschlägt (zufälliger Verlust nur in B)",
                   "fehlende Fenster in B in %", "Anteil in %")


def build_looks(looks, rates):
    """Fehlalarmrate des Zuteilungstests bei mehrfachem Prüfen (kein Verlust)."""
    fig = go.Figure(go.Bar(x=[str(k) for k in looks], y=[100 * r for r in rates], marker_color=C.COLOR_B))
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="5 %", annotation_position="top left")
    fig.update_yaxes(range=[0, max(35, 100 * max(rates) * 1.1)])
    return _finish(fig, "Fehlalarmrate bei wiederholter Prüfung (ohne jeden Verlust)", "Zahl der Prüfungen", "Anteil in %", height=280)
