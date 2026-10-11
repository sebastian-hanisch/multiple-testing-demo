# Viele Kennzahlen, viele Varianten: Mehrfachtests und Gewinnerfluch – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-multiple-testing-demo.streamlit.app/)**

Interaktive Demo zum **gleichzeitigen Prüfen vieler Varianten**. **Fünftes Stück der Konzepte-Linie „Experimente und
Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning), Kind des [A/B-Tests](https://github.com/sebastian-hanisch/ab-test-demo): dort ein Vergleich, hier m Varianten von
Regel B gegen Regel A. Das Vehikel ist dasselbe: ein Standort mit täglicher Nachbestellung, Regel A (Sicherheitsfaktor 1,0),
Einheit ist ein Standort-Fenster von vier Wochen, Kennzahl der Servicegrad.

## Kernfrage

Wie oft findet man bei vielen Vergleichen etwas, das nicht da ist, was kosten die Korrekturen an echten Befunden, und was
passiert mit der Schätzung der Gewinner-Variante?

## Modell und Methodik

- **Aufbau:** m Varianten gegen Regel A, die ersten m1 mit echter Wirkung (Sicherheitsfaktor z), die übrigen gleich A. Je
  Vergleich n Fenster je Arm, aus den Pools des ersten Stücks (SplitMix64). Kontrolle **gemeinsam** (ein Arm A für alle,
  abhängige Tests) oder **eigen** je Vergleich (unabhängige Tests).
- **Vier Verfahren** (`mtc_multiple.py`): ohne Korrektur, Bonferroni (p·m), Holm (Schritt für Schritt), Benjamini-Hochberg
  (p·m/i mit laufendem Minimum).
- **Messgrößen:** *mindestens ein Fehlalarm* (familienweise Fehlerrate), *Anteil falscher Entdeckungen* unter allen Meldungen,
  *Teststärke* je echter Variante.
- **Gewinnerfluch** (`winner`): alle k Varianten mit derselben wahren Wirkung; die mit der größten gemessenen Verbesserung wird
  gekürt; eine Wiederholung zieht für sie frische Fenster.
- Der Zufalls-Seed der Voreinstellung (52) ist so gewählt, dass das Einzelexperiment die typische Lage zeigt (ein Fehlalarm
  ohne Korrektur); die Häufigkeiten zeigt die Wiederholung über 1 000 Experimente.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (20 Vergleiche, 30 Fenster je Arm, 3 000 Experimente je Zelle, Fehler der Raten
höchstens 0,9 Prozentpunkte; Gewinnerfluch 4 000 Wiederholungen).

| Frage | Befund |
|---|---|
| Wie oft gibt es bei 20 wirkungslosen Varianten mindestens einen Fehlalarm? | Ohne Korrektur **64,3 %** bei eigener Kontrolle (Theorie 1 − 0,95²⁰ = 64,2 %), **40,4 %** bei gemeinsamer Kontrolle (die Tests sind positiv abhängig). |
| Was halten die Korrekturen? | Bonferroni und Holm **3,6 %** (gemeinsam) bzw. **5,2 %** (eigene Kontrolle); Benjamini-Hochberg **5,2 %**. |
| Was kosten sie an Teststärke? | Zwei echte Varianten (Faktor 1,4): ohne Korrektur werden sie in **85,6 %** der Fälle gefunden, mit Bonferroni in **45,1 %**, mit Holm in **45,4 %**, mit Benjamini-Hochberg in **50,5 %**. |
| Wie groß ist der Unterschied zwischen Holm und Bonferroni? | Fast keiner: **0,3 Prozentpunkte** Teststärke bei zwei echten Varianten. |
| Wann lohnt Benjamini-Hochberg? | Bei fünf echten Varianten (eigene Kontrolle): Holm **46,8 %**, Benjamini-Hochberg **62,9 %**. Der Preis: mindestens ein Fehlalarm in **15,0 %** der Experimente, falsche Entdeckungen im Anteil **3,7 %**. |
| Wie viele Meldungen ohne Korrektur sind falsch? | Bei zwei echten unter 20 Varianten sind im Mittel **21 %** (gemeinsame) bzw. **28 %** (eigene Kontrolle) der Meldungen falsch; bei fünf echten **13 %**. |
| Und bei kleinen Effekten? | Faktor 1,2 mit fünf echten Varianten: ohne Korrektur **34,6 %** Teststärke und **28 %** falsche Meldungen, mit Bonferroni **6,3 %**, mit Benjamini-Hochberg **8,2 %**. Die Korrektur nimmt fast alles. |
| Wie groß ist der Gewinnerfluch ohne jede Wirkung? | Die beste von 10 Varianten misst im Mittel **+1,4 Prozentpunkte**, von 30 **+1,8**; sie ist in **15 %** bzw. **26 %** der Experimente „signifikant“ (mit Bonferroni-Schwelle **1,7 %**) und bestätigt sich in einer Wiederholung nur in **2 %**. |
| Und bei gleichen echten Effekten? | Wirkung **1,96 Punkte**: die beste von 10 misst **3,15** (das **1,6-Fache**), von 50 **3,62**; frisch gemessen wieder **1,97**. Bestätigt wird sie in **35 %**, wie ein einzelner Test. |
| Bei klarem Effekt? | Faktor 1,4 (3,49 Punkte): die beste von 10 misst das **1,28-Fache**. |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Zahlen der Vorab-Messreihe auf dem Terminal-Gate** lagen darunter: dort 58,7 % statt 64,2 %, weil der Welch-Test auf den
  schiefen Tagesmitteln im Tail konservativ war. Auf diesem Vehikel stimmt die Theorie (64,3 %).
- **Holm gegen Bonferroni ist ein Randbefund** (0,3 Punkte), Benjamini-Hochberg der eigentliche Unterschied; im Plan stand
  „Holm/BH“ als gleichwertige Hälften.
- **Benjamini-Hochberg hält die Fehlalarmrate nicht**, nur den Anteil falscher Entdeckungen: bei fünf echten Varianten gibt es in
  15 % der Experimente mindestens einen Fehlalarm. Wer „kein einziger Fehlalarm“ braucht, bleibt bei Holm.
- **Die Korrektur repariert den Gewinnerfluch nicht.** Sie schützt die Fehlalarmrate; die Schätzung des Gewinners bleibt
  überschätzt (1,6-fach). Erst die Wiederholungsmessung ist unverzerrt.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Zahl der Vergleiche steht vorher fest** | Nachträglich ausgewählte Varianten oder Kennzahlen sind mehr Vergleiche, als man zählt. | (dieses Stück) |
| **Eine Korrektur reicht** | Sie schützt die Fehlalarmrate, nicht die Schätzung. | (dieses Stück) |
| **Man blickt nur einmal** | Mehrere Blicke je Variante vervielfachen die Tests. | Zwischenblicke und dauerndes Hinsehen |
| **Unabhängig oder positiv abhängig** | Benjamini-Hochberg ist dafür bewiesen; bei beliebiger Abhängigkeit braucht es die strengere Variante. | (nicht Teil der Linie) |
| **Einheiten unabhängig und gleichartig** | Verhältniskennzahlen und Cluster vergrößern die Streuung jedes Vergleichs. | Verhältniskennzahlen und Cluster |
| **Die echten Effekte sind gleich groß** | Hier haben alle echten Varianten dieselbe Wirkung; bei verschiedenen Wirkungen ist die Auswahl teilweise berechtigt. | Bandit statt A/B |

Die Zahlen gelten für dieses erfundene Vehikel mit unabhängigen Fenstern; die Bayes'sche Schrumpfung der Schätzungen und
Subgruppen-Analysen sind nicht Teil der Demo.

## Bezug zu OR

Eine Disponentin, die zwanzig Parameter-Varianten einer Regel im Pilot testet und die beste einführt, hat zwanzig Vergleiche
gemacht. Die Demo zeigt, wie viel von dem, was sie in der Pilotphase gesehen hat, nur Auswahl war, und wie viel der Schutz
davor an echter Wirkung kostet.

## Verwandte Demos im Portfolio

- [ab-test-demo](https://github.com/sebastian-hanisch/ab-test-demo), [test-power-demo](https://github.com/sebastian-hanisch/test-power-demo),
  [sample-ratio-demo](https://github.com/sebastian-hanisch/sample-ratio-demo),
  [sequential-test-demo](https://github.com/sebastian-hanisch/sequential-test-demo): die ersten Stücke der Linie.
- [bandit-demo](https://github.com/sebastian-hanisch/bandit-demo): Auswahlverfahren mit Regret, ohne Korrektur für die Auswahl.

## Verifikation

- **Korrekturen** (`tests/test_multiple.py`, `tests/test_oracle_multiple_testing.py`): von Hand; Benjamini-Hochberg gegen
  `scipy.stats.false_discovery_control`; Holm gegen geschlossenes Testen mit Bonferroni-Lokaltests über alle Teilmengen;
  Ordnung Bonferroni ≤ Holm ≤ Benjamini-Hochberg in den Ablehnungen.
- **Experimente:** Welch-Test gegen `scipy.stats.ttest_ind`; gemeinsame Kontrolle macht die Tests positiv abhängig, eigene nicht;
  familienweise Fehlerrate unabhängiger Tests gegen 1 − 0,95^m.
- **Gewinnerfluch:** gegen eine unabhängige Schleife mit anderem Zufallsgenerator.
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Experiment mit sortierten p-Werten, tausend Wiederholungen, Gewinnerfluch, Grenzen |
| `mtc_constants.py` | Vehikel-Konstanten, Regler-Grenzen, Verfahren, Presets |
| `mtc_rng.py`, `mtc_vehicle.py`, `mtc_formulas.py`, `mtc_stats.py` | Zufall, Standort-Fenster, exakter Servicegrad, Welch-Test (aus dem ersten Stück) |
| `mtc_multiple.py` | Bonferroni, Holm, Benjamini-Hochberg (angepasste p-Werte) |
| `mtc_evaluation.py` | Experimente mit m Vergleichen, Zusammenfassungen, Gewinnerfluch |
| `mtc_presets.py`, `mtc_visualization.py` | Permalink, Presets; Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_pools.json` | vorgerechnete Pools (je 10 000 Fenster) |
| `tools/measure_stueck5.py` | die Messreihe vor dem Text |
| `tests/` | Vehikel, Orakel, Korrekturen, Experimente, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Verfahren für beliebige Abhängigkeit** (Benjamini-Yekutieli) und **Hochberg/Hommel:** nicht gebaut.
- **Hierarchische oder Bayes'sche Schrumpfung** der Schätzungen gegen den Gewinnerfluch: nicht gebaut.
- **Subgruppen-Analysen:** der klassische Fall mehrfacher Tests, hier nicht gezeigt.

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
