"""Gültigkeit der Zuteilung - A/A-Test und Sample-Ratio-Mismatch - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Im A/B-Test des ersten Stücks lief die Zuteilung
makellos. Hier gehen nach der Zuteilung Fenster verloren, und es wird gemessen, was der Zuteilungstest (Sample-Ratio-
Mismatch) davon bemerkt, was der Effekttest davon verzerrt und was keiner von beiden sieht. Siehe README.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import srm_constants as C
from srm_evaluation import (exact_size, load_pools, nearest_z, repeated_look_false_alarm, run_one, srm_power_by_loss,
                            summarize, true_effect)
from srm_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from srm_stats import srm_test
from srm_visualization import build_counts, build_histogram, build_interval, build_looks, build_srm_power

st.set_page_config(page_title="Zuteilung prüfen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _pools():
    return load_pools()


@st.cache_data(show_spinner=False)
def _one(z, n, loss, mech, seed):
    return run_one(_pools(), {"z": z, "n": n, "loss": loss, "mech": mech, "seed": seed})


@st.cache_data(show_spinner=False)
def _many(z, n, loss, mech):
    return summarize(_pools(), z, n, loss, mech, reps=C.LIVE_REPS)


@st.cache_data(show_spinner=False)
def _curves(ns):
    losses = [x / 100 for x in range(0, 21, 2)]
    return {n: list(zip([int(round(100 * f)) for f in losses], srm_power_by_loss(n, losses))) for n in ns}


@st.cache_data(show_spinner=False)
def _power_at(n, loss):
    return srm_power_by_loss(n, [loss / 100])[0]


@st.cache_data(show_spinner=False)
def _looks(n):
    ks = (1, 2, 5, 10, 30)
    return ks, [repeated_look_false_alarm(n, k, 4000, 4242) for k in ks]


st.title("⚖️ Gültigkeit der Zuteilung: lief das Experiment wie geplant?")
st.markdown(
    """
Im A/B-Test war die Zuteilung makellos: jedes Standort-Fenster wurde ausgewertet. In der Praxis gehen **nach der Zuteilung**
Fenster verloren (ein Standort meldet nicht, eine Auswertung verwirft Ausreißer, ein Fehler im Messaufbau). Der
**Zuteilungstest (Sample-Ratio-Mismatch, SRM)** prüft, ob die Zahl der ausgewerteten Fenster je Arm noch zum geplanten
Verhältnis 1 : 1 passt. Hier lässt sich messen, **was dieser Test bemerkt, was der Effekttest verzerrt und was keiner von
beiden sieht**, weil die wahre Wirkung bekannt ist.
"""
)
st.caption(
    "Drittes Stück der Linie „Experimente und Wirkungsmessung“, aufbauend auf "
    "[ab-test-demo](https://sebastianhanisch-ab-test-demo.streamlit.app/) (gleiches Vehikel: Standort-Fenster, Servicegrad, "
    "Regel A gegen Regel B). Jedes Folgestück hebt eine der Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So funktioniert die Prüfung", expanded=True):
    st.markdown(
        """
- **Zuteilung:** Jedes Fenster geht per Münzwurf an A oder B. Bei 400 Fenstern landen also nicht genau 200 in jedem Arm; die
  Abweichung ist Zufall und genau berechenbar.
- **Verlust nach der Zuteilung:** Ein Anteil der Fenster fehlt in der Auswertung. **Wie** er fehlt, ist der Punkt: zufällig,
  oder gerade die schlechten Fenster, nur in einem Arm oder in beiden.
- **Zuteilungstest (SRM):** Chi-Quadrat-Test, ob die ausgewerteten Zahlen noch zu 1 : 1 passen. Er schlägt an, wenn ein Arm
  deutlich mehr Fenster verloren hat als der andere.
- **Effekttest:** der Welch-Test des ersten Stücks auf den übrig gebliebenen Fenstern. Er sieht nur Mittelwerte, nicht, ob
  etwas fehlt.
- **A/A-Test:** dieselbe Regel in beiden Armen (z = 1,0). Hier gibt es nichts zu finden; jeder Befund ist ein Fehlalarm
  und damit ein Hinweis auf ein Problem im Messaufbau.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{i}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])
st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Wahrheit**")
    z = st.slider("Sicherheitsfaktor z von Regel B", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Regel A fährt z = 1,0. Bei z = 1,0 sind beide Regeln gleich: ein A/A-Test ohne Wirkung.")
    st.markdown("**Experiment**")
    n = st.slider("Fenster insgesamt", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="Gesamtzahl der Fenster, per Münzwurf auf A und B verteilt.")
    st.markdown("**Datenverlust**")
    loss = st.slider("Fehlende Fenster in B in %", *bounds("loss_slider"), step=C.LOSS_STEP, key="loss_slider",
                     help="Soll-Anteil der Fenster, die in der Auswertung fehlen (bezogen auf den betroffenen Arm).")
    mech_index = st.radio("Wie die Fenster fehlen", options=list(range(len(C.MECHANISMS))), key="mech_radio",
                          format_func=lambda i: C.MECH_LABELS[C.MECHANISMS[i]],
                          help="Der Mechanismus entscheidet, ob der Verlust harmlos ist oder verzerrt.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt Zuteilung und Ergebnisse des einen Experiments oben.")
    st.button("🎲 Neues Experiment würfeln", on_click=randomize_seed)

z, n, loss, mech_index, seed = nearest_z(float(z)), int(n), int(loss), int(mech_index), int(seed)
mech = C.MECHANISMS[mech_index]
sync_query_params({"z_slider": z, "n_slider": n, "loss_slider": loss, "mech_radio": mech_index, "seed_input": seed})
st.sidebar.caption(C.MECH_HELP[mech])

pools = _pools()
truth = true_effect(pools, z)
aa = z <= C.Z_A

# --- Ein Experiment --------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 🧪 Ein Experiment")
one = _one(z, n, loss, mech, seed)
assigned_b = int(one["assigned_b"])
assigned_a = n - assigned_b
kept_a, kept_b = int(one["n_a"]), int(one["n_b"])
chi2, srm_p = srm_test(kept_a, kept_b)
srm_p = float(srm_p)
est, p_eff = float(one["diff"]), float(one["p"])
st.caption(
    f"{C.fmt_int(n)} Fenster, per Münzwurf verteilt; Regel B mit z = {C.fmt_num(z)}"
    + (" (gleich wie A)" if aa else f", wahre Wirkung **{C.fmt_pp(truth)}**")
    + f". Verlust: {loss} % in B, {C.MECH_LABELS[mech].lower()}."
)
row1, row2 = st.columns(2), st.columns(2)
row1[0].metric("Zugeteilt (A / B)", f"{assigned_a} / {assigned_b}")
row1[1].metric("Ausgewertet (A / B)", f"{kept_a} / {kept_b}")
row2[0].metric("Zuteilungstest, p-Wert", C.fmt_p(srm_p), delta="Alarm" if srm_p < C.ALPHA else "still", delta_color="off",
               delta_arrow="off", help="Chi-Quadrat-Test auf das Verhältnis 1 : 1 der ausgewerteten Fenster.")
row2[1].metric("Effekttest, p-Wert", C.fmt_p(p_eff) if np.isfinite(p_eff) else "–",
               delta=("signifikant" if p_eff < C.ALPHA else "nicht signifikant") if np.isfinite(p_eff) else None,
               delta_color="off", delta_arrow="off",
               help="Welch-Test auf die ausgewerteten Fenster; geschätzte Differenz: " + (C.fmt_pp(est) if np.isfinite(est) else "–"))
left, right = st.columns(2)
with left:
    st.plotly_chart(build_counts(assigned_a, assigned_b, kept_a, kept_b), width="stretch",
                    key=f"counts_{z}_{n}_{loss}_{mech}_{seed}")
with right:
    st.plotly_chart(build_interval(est, float(one["lo"]), float(one["hi"]), truth), width="stretch",
                    key=f"interval_{z}_{n}_{loss}_{mech}_{seed}")
    st.caption(f"Geschätzte Differenz: {C.fmt_pp(est) if np.isfinite(est) else '–'}; wahre Wirkung: {C.fmt_pp(truth)}.")
if srm_p < C.ALPHA:
    st.warning(f"**Der Zuteilungstest schlägt an (p = {C.fmt_p(srm_p)}):** {kept_a} gegen {kept_b} ausgewertete Fenster passen "
               "nicht zu 1 : 1. Bevor man den Effekt liest, müsste man klären, wo die Fenster geblieben sind.")
else:
    st.info(f"Der Zuteilungstest bleibt still (p = {C.fmt_p(srm_p)}): {kept_a} gegen {kept_b} ausgewertete Fenster sind mit "
            "einer fairen Münzwurf-Zuteilung vereinbar. Das beweist nicht, dass nichts fehlt.")

# --- Viele Experimente -----------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📐 Tausend Experimente: was sehen die Tests wirklich?")
many = _many(z, n, loss, mech)
cols = st.columns(2)
cols[0].metric("Zuteilungstest schlägt an", C.fmt_pct(many["srm_alarm"]),
               help="Anteil der Experimente mit p unter 0,05. Ohne jeden Verlust sind es etwa 5 %.")
cols[1].metric("… mit strenger Schwelle (0,001)", C.fmt_pct(many["srm_alarm_strict"]),
               help="In der Praxis wird oft eine strengere Schwelle gewählt, damit der Test nicht ständig anschlägt.")
cols2 = st.columns(2)
cols2[0].metric("Effekttest meldet Unterschied" if aa else "Effekttest signifikant", C.fmt_pct(many["effect_reject"]),
                help="Bei z = 1,0 ist jeder Befund ein Fehlalarm (Soll 5 %).")
cols2[1].metric("Mittlere Verzerrung der Schätzung", C.fmt_pkt(many["bias"], 2),
                help="Mittlere Schätzung minus wahre Wirkung, in Prozentpunkten.")
st.plotly_chart(build_histogram(many["diffs"], many["p"] < C.ALPHA, truth), width="stretch", key=f"hist_{z}_{n}_{loss}_{mech}")

lost_b, lost_a = many["lost_share_b"], many["lost_share_a"]
parts = []
if aa:
    parts.append(f"Beide Regeln sind gleich. Der Effekttest meldet trotzdem in **{C.fmt_pct(many['effect_reject'])}** der "
                 "Experimente einen Unterschied (Soll 5 %).")
else:
    rel = f" ({C.fmt_pct(abs(many['bias_rel']), 0)} {'zu groß' if many['bias'] > 0 else 'zu klein'})" if abs(many["bias_rel"]) >= 0.01 else ""
    parts.append(f"Die Schätzung liegt im Mittel bei {C.fmt_pp(many['mean_estimate'])} statt {C.fmt_pp(truth)}: Verzerrung "
                 f"**{C.fmt_pp(many['bias'])}**{rel}.")
parts.append(f"Der Zuteilungstest schlägt in **{C.fmt_pct(many['srm_alarm'])}** an. In B fehlen im Mittel {C.fmt_pct(lost_b)}, in "
             f"A {C.fmt_pct(lost_a)} der Fenster.")
distorted = (aa and many["effect_reject"] > 0.08) or ((not aa) and abs(many["bias"]) >= 0.0010)
if distorted and many["srm_alarm"] < 0.5:
    parts.append("**Die Verzerrung bleibt in den meisten Experimenten unbemerkt.**")
    st.error(" ".join(parts))
elif distorted:
    st.warning(" ".join(parts))
else:
    parts.append("Hier ist der Verlust harmlos: die Schätzung bleibt unverzerrt." if loss > 0 else "Ohne Verlust gibt es nichts zu finden.")
    st.success(" ".join(parts))

# --- Wie gut sieht der Zuteilungstest einen Verlust? ------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔭 Wie viel Verlust bemerkt der Zuteilungstest?")
ns = tuple(sorted({100, 400, 2000, n}))
st.markdown(
    "Der Zuteilungstest sieht nur **Unterschiede in den Zahlen**, und bei wenigen Fenstern sind schon faire Münzwürfe "
    "unruhig. Die Kurven zeigen den Anteil der Experimente, in denen er anschlägt, wenn in B zufällig ein Teil der Fenster "
    "fehlt (exakt berechnet)."
)
with st.spinner("Rechne …"):
    curves = _curves(ns)
st.plotly_chart(build_srm_power(curves, n, loss), width="stretch", key=f"srmpower_{n}")
power_here = _power_at(n, loss)
if loss == 0:
    st.info(f"Ohne Verlust schlägt der Zuteilungstest bei {C.fmt_int(n)} Fenstern in {C.fmt_pct(power_here)} der Experimente an: "
            "das ist der Fehlalarm, den der Münzwurf allein erzeugt.")
else:
    st.info(
        f"Bei {C.fmt_int(n)} Fenstern und {loss} % zufällig fehlenden Fenstern in B schlägt der Test in "
        f"**{C.fmt_pct(power_here, 0)}** der Experimente an. Ein Verlust, der den Effekt schon verfälscht, ist für ihn bei "
        "dieser Größe oft unsichtbar."
    )
st.markdown("**Und wenn man oft hinsieht?** Wer den Zuteilungstest während der Laufzeit mehrfach prüft, bekommt mehrfach die "
            "Chance auf einen Fehlalarm.")
ks, rates = _looks(n)
st.plotly_chart(build_looks(ks, rates), width="stretch", key=f"looks_{n}")
st.caption(f"Bei {C.fmt_int(n)} Fenstern und {ks[-1]} Prüfungen schlägt der Test in {C.fmt_pct(rates[-1], 0)} der Experimente "
           "mindestens einmal an, obwohl nichts verloren ging. Einmalige Prüfung am Ende (Sollwert 5 %; exakt "
           f"{C.fmt_pct(exact_size(n))}).")

# --- Grenzen ---------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt nur zufällige Ausfälle** | Hängt der Verlust vom Ergebnis ab, verzerrt er den Effekt; der Zuteilungstest sieht ihn nur bei vielen Fenstern oder großem Verlust. | (dieses Stück) |
| **Der Zuteilungstest bemerkt, was zählt** | Gleicher Verlust in beiden Armen ist für ihn unsichtbar, schwächt aber die Wirkung. | (dieses Stück) |
| **Der Umfang steht vorher fest** | Wiederholtes Prüfen des Zuteilungstests oder des Effekts erzeugt zusätzliche Fehlalarme. | Zwischenblicke und dauerndes Hinsehen |
| **Ein Test, eine Kennzahl** | Viele Kennzahlen brauchen jede eine eigene Gültigkeitsprüfung. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Einheiten unabhängig und gleichartig** | Bei Clustern oder Serienkorrelation passt die einfache Münzwurf-Annahme nicht. | Verhältniskennzahlen und Cluster |
| **Die Einheiten beeinflussen sich nicht** | Zuteilung allein sagt nichts darüber, ob A- und B-Standorte sich gegenseitig beeinflussen. | Interferenz und Switchback |
"""
)
st.caption(
    "Die Zahlen stammen aus dem erfundenen Vehikel dieses Stücks. Die vier Verlustmechanismen sind Modelle möglicher "
    "Ursachen, keine Beobachtung aus einem Betrieb."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Zuteilungstest.** Bei Münzwurf-Zuteilung ist die Zahl $n_B$ der Fenster in B binomial mit $N$ und $1/2$. Der
Chi-Quadrat-Test prüft die ausgewerteten Zahlen $(n_A, n_B)$ gegen das Verhältnis 1 : 1:
$\chi^2 = (n_A - n/2)^2/(n/2) + (n_B - n/2)^2/(n/2)$ mit einem Freiheitsgrad. Wegen der diskreten Verteilung ist die
Fehlalarmrate bei kleinem $N$ nicht genau $\alpha$; hier wird sie durch Aufzählung angegeben.

**Entdeckungswahrscheinlichkeit.** Geht in B zufällig der Anteil $f$ verloren, sind die ausgewerteten Fenster von B
binomial mit $n_B$ (zugeteilt) und $1-f$. Die Wahrscheinlichkeit, dass $\chi^2$ über dem Schwellenwert liegt, wird über alle
$n_B$ aufsummiert (`srm_power_by_loss`).

**Mechanismen.** Zufällig: Fenster von B fallen unabhängig vom Ergebnis mit Wahrscheinlichkeit $f$ weg. Schlechteste: Fenster von
B unter dem $f$-Quantil der B-Verteilung. Symmetrisch: in jedem Arm unter dem $f$-Quantil der eigenen Verteilung. Grenzwert:
in beiden Armen unter dem $f$-Quantil von A. Verzerrung = Mittel der Schätzung minus wahre Wirkung (Mittel der Pools).

**Wiederholte Prüfung.** Bei $K$ Prüfungen auf dem sich füllenden Experiment ist die Fehlalarmrate die Wahrscheinlichkeit,
dass mindestens ein $\chi^2_k$ den Schwellenwert übersteigt; sie wächst mit $K$.

Implementiert in `srm_evaluation.py` (Zuteilung, Verlust, beide Tests, exakte Raten), `srm_stats.py` (Chi-Quadrat, Welch aus
Momenten), `srm_vehicle.py` (Standort-Fenster), `generate_precomputed.py` (Pools).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
