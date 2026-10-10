"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort-Fenster) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # Dispersion der negativ-binomialen Tagesnachfrage (ganzzahlig: Gamma(5) = Summe von 5 Exponentialzahlen)
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor dem Auswertefenster (gleiche Regel wie im Fenster)
WINDOW_DAYS = 28          # Auswertefenster: vier Wochen = ein "Standort-Fenster" = eine Einheit des Experiments
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A

Z_MIN, Z_MAX, DEFAULT_Z = 1.0, 2.0, 1.4      # Regel B: Sicherheitsfaktor (1,0 = identisch mit A = A/A-Test)
Z_STEP = 0.1
Z_GRID = tuple(round(Z_MIN + i * Z_STEP, 1) for i in range(int(round((Z_MAX - Z_MIN) / Z_STEP)) + 1))
POOL_SIZE = 10000         # Einheiten je Pool (je Sicherheitsfaktor)
ALPHA = 0.05
SRM_ALPHA_STRICT = 0.001  # in der Praxis oft verwendete strenge Schwelle für den SRM-Alarm

# Stück 3: Zuteilung und Datenverlust
N_MIN, N_MAX, DEFAULT_N, N_STEP = 40, 2000, 400, 40      # Fenster insgesamt, per Münzwurf auf A und B verteilt
LOSS_MIN, LOSS_MAX, DEFAULT_LOSS, LOSS_STEP = 0, 20, 5, 1   # Anteil der in der Auswertung fehlenden Fenster in Prozent
MECHANISMS = ("zufaellig", "schlechteste", "symmetrisch", "grenzwert")
MECH_LABELS = {
    "zufaellig": "Zufällig, nur in B",
    "schlechteste": "Die schlechtesten Fenster fehlen, nur in B",
    "symmetrisch": "Die schlechtesten fehlen in beiden Armen gleich",
    "grenzwert": "Ein fester Grenzwert für beide Arme",
}
MECH_HELP = {
    "zufaellig": "Jedes Fenster von B geht unabhängig vom Ergebnis mit gleicher Wahrscheinlichkeit verloren (z. B. Übertragungsfehler).",
    "schlechteste": "Fenster von B mit besonders niedrigem Servicegrad werden nicht gemeldet (z. B. Standort meldet bei Engpass nicht).",
    "symmetrisch": "In beiden Armen fallen die schlechtesten Fenster weg, je gemessen an der eigenen Verteilung: gleich viele je Arm.",
    "grenzwert": "Beide Arme verlieren Fenster unter demselben Servicegrad-Grenzwert: der bessere Arm verliert weniger.",
}
SEED_MAX, DEFAULT_SEED = 999999, 35
LIVE_REPS = 1000          # Wiederholungen der Live-Auswertung (aus dem Pool gezogen)

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"

PRESETS = {
    "Die schlechtesten Fenster fehlen in B (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "loss": DEFAULT_LOSS, "mech": 1,
                                                                "seed": DEFAULT_SEED},
    "Harmloser Verlust (zufällig)": {"z": DEFAULT_Z, "n": DEFAULT_N, "loss": 5, "mech": 0, "seed": DEFAULT_SEED},
    "Kein Effekt, aber ein Befund (A/A)": {"z": 1.0, "n": DEFAULT_N, "loss": 3, "mech": 1, "seed": DEFAULT_SEED},
    "Gleicher Verlust, stiller Alarm": {"z": DEFAULT_Z, "n": DEFAULT_N, "loss": 5, "mech": 2, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Die schlechtesten Fenster fehlen in B (Voreinstellung)": "Wirkung 3,5 Punkte, 5 % der Fenster von B fehlen, und zwar die schlechtesten: der Effekttest sieht einen Effekt, der zu groß ist.",
    "Harmloser Verlust (zufällig)": "5 % der Fenster von B gehen zufällig verloren: der Zuteilungstest schlägt manchmal an, die Schätzung bleibt unverzerrt.",
    "Kein Effekt, aber ein Befund (A/A)": "Beide Regeln sind gleich, 3 % der schlechtesten Fenster von B fehlen: der Effekttest findet einen Unterschied, der nicht existiert.",
    "Gleicher Verlust, stiller Alarm": "In beiden Armen fallen die schlechtesten Fenster weg: die Zuteilung bleibt im Gleichgewicht, die Wirkung wird trotzdem kleiner geschätzt.",
}


def fmt_pct(x, digits=1):
    """Anteil (0..1) als Prozentzahl mit Dezimalkomma, z. B. 0,934 -> '93,4 %'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def fmt_pp(x, digits=2):
    """Differenz in Prozentpunkten (aus Anteilen 0..1) mit Vorzeichen und Dezimalkomma."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_pkt(x, digits=1):
    """Kurzform für enge Kacheln: '+4,0 Pkt.' (Differenz in Prozentpunkten, aus Anteilen 0..1)."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Pkt."


def fmt_num(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(x):,}".replace(",", " ")


def fmt_p(p):
    """p-Wert: 'unter 0,001' oder drei Nachkommastellen."""
    return "unter 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")
