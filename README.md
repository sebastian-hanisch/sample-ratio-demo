# Gültigkeit der Zuteilung: A/A-Test und Sample-Ratio-Mismatch – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-sample-ratio-demo.streamlit.app/)**

Interaktive Demo zur **Prüfung, ob ein Experiment so lief wie geplant**. **Drittes Stück der Konzepte-Linie „Experimente und
Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning), Kind des [A/B-Tests](https://github.com/sebastian-hanisch/ab-test-demo): dort war die Zuteilung makellos und jedes
Fenster wurde ausgewertet, hier gehen nach der Zuteilung Fenster verloren. Das Vehikel ist dasselbe: ein Standort mit täglicher
Nachbestellung, Regel A (Sicherheitsfaktor 1,0) gegen Regel B, Einheit ist ein Standort-Fenster von vier Wochen, Kennzahl der
Servicegrad.

## Kernfrage

Was bemerkt der **Zuteilungstest (Sample-Ratio-Mismatch, SRM)** von dem, was nach der Zuteilung verloren geht, was verzerrt der
Effekttest, und was sieht keiner von beiden?

## Modell und Methodik

- **Zuteilung:** jedes von N Fenstern geht per Münzwurf an A oder B; die Fenster stammen aus den Pools des ersten Stücks (je
  10 000 simulierte Fenster je Sicherheitsfaktor, SplitMix64), die Wahrheit ist das Poolmittel.
- **Datenverlust nach der Zuteilung** (`loss_mask`), Anteil f:
  - *Zufällig, nur in B:* jedes Fenster von B fällt unabhängig vom Ergebnis mit Wahrscheinlichkeit f weg.
  - *Die schlechtesten Fenster fehlen, nur in B:* Fenster von B unter dem f-Quantil der Verteilung von B.
  - *Die schlechtesten fehlen in beiden Armen gleich:* je Arm unter dem f-Quantil der eigenen Verteilung.
  - *Fester Grenzwert für beide Arme:* beide Arme verlieren Fenster unter dem f-Quantil von A; der bessere Arm verliert weniger.
- **Zuteilungstest:** Chi-Quadrat-Test der ausgewerteten Zahlen auf das Verhältnis 1 : 1 (`srm_test`), dazu die **exakte**
  Fehlalarmrate durch Aufzählung der Binomialverteilung (`exact_size`) und die **exakte** Entdeckungswahrscheinlichkeit bei
  zufälligem Verlust (`srm_power_by_loss`).
- **Effekttest:** Welch-Test des ersten Stücks auf den übrig gebliebenen Fenstern (aus Momenten, vektorisiert).
- **Verzerrung** = Mittel der Schätzung über viele Experimente minus wahre Wirkung.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (3 000 Experimente je Zelle, Fehler der Raten höchstens 0,8 Prozentpunkte; exakte
Werte ohne Streuung). Wahre Wirkung bei Sicherheitsfaktor 1,4: **3,49 Prozentpunkte** Servicegrad.

| Frage | Befund |
|---|---|
| Hält der Zuteilungstest sein Niveau? | Bei Münzwurf-Zuteilung ist die exakte Fehlalarmrate **3,85 %** bei 40 Fenstern, **5,69 %** bei 100 und **5,1 bis 5,2 %** ab 400. Mit der strengen Schwelle 0,001 sind es etwa **0,1 %**. |
| Wie oft sieht man hin? | Bei 400 Fenstern schlägt er bei 2 Prüfungen in **9 %** der Experimente an, bei 5 in **14 %**, bei 10 in **19 %**, bei 30 in **28 %**, obwohl nichts fehlt. |
| Wie viel zufälligen Verlust bemerkt er? | Bei 400 Fenstern und 5 % fehlenden Fenstern in B nur in **8,1 %** der Experimente, bei 10 % in **17,4 %**, bei 20 % in **55,9 %**. Bei 2 000 Fenstern: 5 % → **20,5 %**, 10 % → **63,1 %**, 20 % → **99,7 %**. |
| Ist zufälliger Verlust schlimm? | Nein. Er verzerrt die Schätzung nicht (unter 0,06 Prozentpunkte). |
| Was, wenn die schlechten Fenster von B fehlen (A/A, ohne Wirkung)? | Bei 400 Fenstern und 2 % Verlust meldet der Effekttest in **10,0 %** der Experimente einen Unterschied, bei 5 % in **26,8 %** (Soll 5 %), der Zuteilungstest nur in **5,8 %** bzw. **7,2 %**. Verzerrung **+0,33** bzw. **+0,66 Prozentpunkte**. |
| Bei mehr Fenstern? | Bei 2 000 Fenstern und 5 % meldet der Effekttest in **87 %** der Experimente einen Unterschied, der Zuteilungstest in **21 %**. |
| Und mit echter Wirkung (3,49 Punkte)? | Fehlen die schlechtesten Fenster von B (5 %), ist die Wirkung um **0,52 Punkte (15 %)** zu groß geschätzt; der Test ist ohnehin signifikant und merkt nichts. |
| Gleicher Verlust in beiden Armen? | Die Zuteilung bleibt im Gleichgewicht: der Zuteilungstest schlägt in **5,0 %** an (wie ohne Verlust). Die Wirkung wird um **0,13 Punkte (4 %)** zu klein geschätzt. |
| Fester Grenzwert für beide Arme? | Der bessere Arm verliert weniger (**0,6 %** gegen **5,1 %** der Fenster); die Wirkung wird um **0,56 Punkte (16 %)** zu klein geschätzt. Der Zuteilungstest schlägt bei 400 Fenstern in **7,9 %** an, bei 2 000 Fenstern in **16,4 %**: der Effekt selbst erzeugt den Alarm. |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vorab-Messreihe auf dem Terminal-Gate** (Tage à 100 Lkw, 10 000 Einheiten) fand dasselbe Muster mit anderen Größen:
  Dort bemerkte der Zuteilungstest 2 % Verlust in 17 % der Fälle, hier bei den üblichen 400 Fenstern nur etwa 5 %. Wichtig ist die
  **Zahl der Einheiten**: bei Standort-Fenstern sind es Hunderte, nicht Zehntausende.
- **Die Erwartung „SRM findet, was der Effekttest nicht sieht“ ist umgekehrt.** Im A/A-Test ist der Effekttest die
  empfindlichere Sicherung gegen ergebnisabhängigen Verlust (26,8 % gegen 7,2 %). Der Zuteilungstest ist ein grober Rauchmelder.
- **Ein Alarm kann vom Effekt selbst kommen** (fester Grenzwert): dann ist es kein Datenfehler, aber die Schätzung ist
  trotzdem zu klein.
- **Wirkung gleich Null ist der Testfall.** Im A/A-Test zeigt sich der Messfehler ohne Wirkung am deutlichsten; ein A/A-Test vor
  dem Experiment ist deshalb kein Selbstzweck.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt nur zufällige Ausfälle** | Hängt der Verlust vom Ergebnis ab, verzerrt er den Effekt und bleibt oft unbemerkt. | (dieses Stück) |
| **Der Zuteilungstest bemerkt, was zählt** | Gleicher Verlust in beiden Armen ist für ihn unsichtbar, schwächt aber die Wirkung. | (dieses Stück) |
| **Der Umfang steht vorher fest** | Wiederholtes Prüfen erzeugt zusätzliche Fehlalarme. | Zwischenblicke und dauerndes Hinsehen |
| **Ein Test, eine Kennzahl** | Viele Kennzahlen brauchen je eine Gültigkeitsprüfung. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Einheiten unabhängig und gleichartig** | Bei Clustern passt die einfache Münzwurf-Annahme nicht. | Verhältniskennzahlen und Cluster |
| **Die Einheiten beeinflussen sich nicht** | Zuteilung allein sagt nichts über gegenseitigen Einfluss. | Interferenz und Switchback |

Die vier Mechanismen sind Modelle möglicher Ursachen, keine Beobachtung aus einem Betrieb. Die Zahlen gelten für dieses
erfundene Vehikel.

## Bezug zu OR

In jedem Pilotbetrieb gehen Messwerte verloren: ein Standort meldet nicht, eine Schicht fehlt, ein System verwirft Ausreißer.
Wer die Regel bewertet, braucht die Auskunft, ob der Verlust den Vergleich verzerrt. Das Stück macht aus „es fehlen ein paar
Datensätze“ eine Prüfung mit bekannter Trennschärfe.

## Verwandte Demos im Portfolio

- [ab-test-demo](https://github.com/sebastian-hanisch/ab-test-demo): das erste Stück der Linie (Vehikel, Welch-Test, Abdeckung).
- [test-power-demo](https://github.com/sebastian-hanisch/test-power-demo): das zweite Stück (Teststärke, Planung aus einem Pilot).
- [output-analysis-demo](https://github.com/sebastian-hanisch/output-analysis-demo): Gültigkeit von Intervallen aus einem
  Simulationslauf, nicht von Zuteilungen.

## Verifikation

- **Vehikel, Zufall, Test:** wie im ersten Stück (Mini-Instanz von Hand, SplitMix64-Referenzwerte, Welch gegen scipy).
- **Zuteilungstest:** von Hand (60 gegen 40: χ² = 4,0, p = 0,0455), gegen `scipy.stats.chisquare`; exakte Fehlalarmrate gegen die
  Simulation des Münzwurfs; exakte Entdeckungswahrscheinlichkeit gegen die vektorisierte Simulation.
- **Mechanismen:** Verlustmasken an einer Mini-Instanz von Hand; Erhaltung der Fenster (ausgewertet plus verloren gleich
  zugeteilt); jede Variante ändert das Ergebnis.
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Experiment, tausend Wiederholungen, Trennschärfe des Zuteilungstests, Grenzen |
| `srm_constants.py` | Vehikel-Konstanten, Regler-Grenzen, Mechanismen, Presets |
| `srm_rng.py`, `srm_vehicle.py`, `srm_formulas.py` | Zufall, Standort-Fenster, exakter Servicegrad (aus dem ersten Stück) |
| `srm_stats.py` | Welch-Test (auch aus Momenten), Normalformel, Zuteilungstest |
| `srm_evaluation.py` | Zuteilung, Verlustmechanismen, beide Tests, exakte Raten, wiederholte Prüfung |
| `srm_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `srm_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_pools.json` | vorgerechnete Pools (je 10 000 Fenster) |
| `tools/measure_stueck3.py` | die Messreihe vor dem Text |
| `tests/` | Vehikel, Orakel, Zuteilungstest, Mechanismen, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Mehr als zwei Arme** und **ungleiche Zuteilungsverhältnisse:** der Test kann das (Parameter `share_a`), die Demo zeigt es nicht.
- **Ursachenanalyse eines Alarms** (welche Standorte fehlen, in welcher Woche): eigenes Thema.
- **Ausgleichsverfahren für fehlende Daten** (Gewichtung, Imputation): nicht gebaut.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Verteilungsfunktionen).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html).
