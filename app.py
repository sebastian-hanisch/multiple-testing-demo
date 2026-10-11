"""Mehrfachtests und Gewinnerfluch - viele Kennzahlen, viele Varianten - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünftes Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Wer viele Varianten oder Kennzahlen gleichzeitig
prüft, findet mit hoher Wahrscheinlichkeit irgendetwas Signifikantes. Vier Verfahren (ohne Korrektur, Bonferroni, Holm,
Benjamini-Hochberg) treten gegeneinander an, dazu der Gewinnerfluch: die beste von k gleich guten Varianten wird
überschätzt. Wahrheit bekannt, deshalb messbar. Siehe README.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import mtc_constants as C
from mtc_evaluation import load_pools, nearest_z, run_one, summarize, true_effect, winner
from mtc_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from mtc_visualization import build_rates, build_sorted_p, build_winner

st.set_page_config(page_title="Mehrfachtests – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _pools():
    return load_pools()


@st.cache_data(show_spinner=False)
def _one(m, m1, z, n, shared, seed):
    return run_one(_pools(), {"m": m, "m1": m1, "z": z, "n": n, "shared": shared, "seed": seed})


@st.cache_data(show_spinner=False)
def _many(m, m1, z, n, shared):
    r = summarize(_pools(), m, m1, z, n, reps=C.LIVE_REPS, shared=shared)
    return {k: r[k] for k in ("rows", "truth", "m", "m1", "z", "n", "shared")}


@st.cache_data(show_spinner=False)
def _winner_curve(z, n):
    pools = _pools()
    return [winner(pools, k, z, n, reps=C.LIVE_REPS) for k in C.K_CURVE]


st.title("🎰 Viele Kennzahlen, viele Varianten: Mehrfachtests und Gewinnerfluch")
st.markdown(
    """
Wer **eine** Variante testet, akzeptiert 5 % Fehlalarm. Wer **zwanzig** testet, bekommt bei lauter wirkungslosen Varianten
im Mittel einen Fehlalarm, und mit großer Wahrscheinlichkeit mindestens einen. Die Demo prüft m Varianten von Regel B
gegen Regel A, von denen nur einige wirklich wirken, und misst für vier Vorgehensweisen, **wie oft sie falsch anschlagen**
und **wie viele echte Effekte sie noch finden**. Dazu kommt der **Gewinnerfluch**: wer die *beste* von k Varianten kürt,
überschätzt sie, selbst wenn alle gleich gut sind.
"""
)
st.caption(
    "Fünftes Stück der Linie „Experimente und Wirkungsmessung“, aufbauend auf "
    "[ab-test-demo](https://sebastianhanisch-ab-test-demo.streamlit.app/) und "
    "[test-power-demo](https://sebastianhanisch-test-power-demo.streamlit.app/) (gleiches Vehikel: Standort-Fenster, "
    "Servicegrad, Regel A gegen Regel B). Jedes Folgestück hebt eine der Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So funktionieren die vier Vorgehensweisen", expanded=True):
    st.markdown(
        """
- **Ohne Korrektur:** jeder Vergleich für sich bei p unter 0,05. Mit m Vergleichen ist die Chance auf mindestens einen
  Fehlalarm etwa 1 − 0,95^m (bei unabhängigen Tests).
- **Bonferroni:** Schwelle 0,05 / m für jeden Vergleich. Hält die Wahrscheinlichkeit für **irgendeinen** Fehlalarm bei 5 %,
  kostet aber viel Teststärke.
- **Holm:** sortiert die p-Werte und lockert die Schwelle Schritt für Schritt. Hält dieselbe Garantie, ist nie schlechter als
  Bonferroni.
- **Benjamini-Hochberg:** kontrolliert nicht „irgendein Fehlalarm“, sondern den **Anteil falscher Entdeckungen** unter allen
  Meldungen. Findet mehr, erlaubt aber ab und zu einen Fehlalarm.
- **Gemeinsame Kontrolle:** Alle Varianten werden gegen dieselben Fenster von Regel A verglichen; die Tests sind dann
  abhängig. Mit **eigener Kontrolle je Vergleich** sind sie unabhängig.
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
    st.markdown("**Varianten**")
    m = st.slider("Zahl der Vergleiche m", *bounds("m_slider"), step=1, key="m_slider",
                  help="Varianten von Regel B, jede gegen Regel A verglichen.")
    m1 = st.slider("Davon mit echter Wirkung", *bounds("m1_slider"), step=1, key="m1_slider",
                   help="Diese Varianten haben die Wirkung des Sicherheitsfaktors unten; die übrigen sind gleich Regel A.")
    z = st.slider("Sicherheitsfaktor der echten Varianten", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Je größer, desto größer die echte Wirkung. Bei 1,0 wirkt keine Variante.")
    st.markdown("**Experiment**")
    n = st.slider("Fenster je Arm und Vergleich", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="So viele unabhängige Standort-Fenster hat jeder Arm in jedem Vergleich.")
    shared_index = st.radio("Kontrollgruppe", options=[0, 1], key="shared_radio", format_func=lambda i: C.SHARED_LABELS[i],
                            help="Gemeinsame Kontrolle macht die Tests abhängig, eigene Kontrollen unabhängig.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt die Fenster des einen Experiments unten.")
    st.button("🎲 Neues Experiment würfeln", on_click=randomize_seed)

z, n, m, m1, seed = nearest_z(float(z)), int(n), int(m), int(m1), int(seed)
m1 = min(m1, m)
shared = int(shared_index) == 0
sync_query_params({"z_slider": z, "n_slider": n, "m_slider": m, "m1_slider": m1, "shared_radio": int(shared_index),
                   "seed_input": seed})

pools = _pools()
truth = true_effect(pools, z)
no_effect = (m1 == 0) or (z <= C.Z_A)
m1_eff = 0 if z <= C.Z_A else m1

# --- Ein Experiment ---------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 🧪 Ein Experiment")
one = _one(m, m1_eff, z, n, shared, seed)
rej = one["rejections"]
real = one["real"]
st.caption(
    f"{m} Varianten gegen Regel A, {m1_eff} mit echter Wirkung" + ("" if no_effect else f" ({C.fmt_pp(truth)})") +
    f", {n} Fenster je Arm, {'gemeinsame' if shared else 'eigene'} Kontrolle. Jeder Punkt ist ein Vergleich; "
    "Linien sind die Schwellen der Verfahren."
)
st.plotly_chart(build_sorted_p(one["p"], real), width="stretch", key=f"sortedp_{m}_{m1_eff}_{z}_{n}_{int(shared)}_{seed}")
tbl = ["| Verfahren | Meldungen | davon falsch | davon echt |", "|---|---|---|---|"]
for method in C.METHODS:
    h = rej[method]
    tbl.append(f"| {C.METHOD_LABELS[method]} | {int(h.sum())} | {int(h[~real].sum())} | {int(h[real].sum())} |")
st.markdown("\n".join(tbl))
fa = int(rej["none"][~real].sum())
if fa > 0:
    st.warning(f"Ohne Korrektur melden hier **{int(rej['none'].sum())}** Varianten einen Unterschied, davon sind **{fa}** "
               "wirkungslos. Sieht man nur die Meldungen, kann man sie von den echten nicht unterscheiden.")
else:
    st.info("In diesem Experiment ist keine wirkungslose Variante aufgefallen. Das ist Glück: die Wiederholung unten zeigt, "
            "wie oft das passiert.")

# --- Viele Experimente ----------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📐 Tausend Experimente: was halten die Verfahren?")
many = _many(m, m1_eff, z, n, shared)
rows = many["rows"]
st.plotly_chart(build_rates(rows, m1_eff > 0), width="stretch", key=f"rates_{m}_{m1_eff}_{z}_{n}_{int(shared)}")
head = ["| Verfahren | Mindestens ein Fehlalarm | Falsche Entdeckungen (Anteil) | Teststärke je echter Variante |",
        "|---|---|---|---|"]
for method in C.METHODS:
    r = rows[method]
    power = C.fmt_pct(r["power"]) if m1_eff > 0 else "–"
    head.append(f"| {C.METHOD_LABELS[method]} | {C.fmt_pct(r['fwer'])} | {C.fmt_pct(r['fdr'])} | {power} |")
st.markdown("\n".join(head))
if m - m1_eff > 0:
    st.info(
        f"Bei {m - m1_eff} wirkungslosen Varianten gibt es ohne Korrektur in **{C.fmt_pct(rows['none']['fwer'])}** der "
        f"Experimente mindestens einen Fehlalarm; Bonferroni und Holm halten **{C.fmt_pct(rows['bonferroni']['fwer'])}**, "
        f"Benjamini-Hochberg **{C.fmt_pct(rows['bh']['fwer'])}**."
    )
if m1_eff > 0:
    st.success(
        f"Der Preis der Korrektur ist Teststärke: die {m1_eff} echten Varianten werden ohne Korrektur in "
        f"{C.fmt_pct(rows['none']['power'])} der Fälle gefunden, mit Bonferroni in {C.fmt_pct(rows['bonferroni']['power'])}, "
        f"mit Holm in {C.fmt_pct(rows['holm']['power'])} und mit Benjamini-Hochberg in {C.fmt_pct(rows['bh']['power'])}. "
        "Holm ist fast nie besser als Bonferroni; Benjamini-Hochberg findet mehr, zahlt aber mit gelegentlichen "
        "Fehlalarmen."
    )

# --- Gewinnerfluch ---------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🏆 Die beste Variante: warum der Gewinner zu gut aussieht")
st.markdown(
    "Jetzt haben **alle** k Varianten dieselbe wahre Wirkung (Sicherheitsfaktor der echten Varianten). Man kürt die mit der "
    "größten gemessenen Verbesserung und fragt: was ist sie im Experiment, und was kann sie wirklich?"
)
curve = _winner_curve(z, n)
st.plotly_chart(build_winner(curve, truth, m), width="stretch", key=f"winner_{z}_{n}_{m}")
here = next((c for c in curve if c["k"] == min(C.K_CURVE, key=lambda k: abs(k - m))), curve[-1])
if z > C.Z_A:
    st.info(
        f"Bei {here['k']} gleich guten Varianten misst die beste im Mittel **{C.fmt_pp(here['mean_winner'])}**, die wahre "
        f"Wirkung ist **{C.fmt_pp(truth)}**; frisch gemessen sind es {C.fmt_pp(here['mean_replication'])}. Die Schätzung der "
        f"gekürten Variante ist also das **{C.fmt_num(here['mean_winner'] / truth)}-Fache**. Signifikant (p unter 0,05) ist der "
        f"Gewinner in {C.fmt_pct(here['winner_sig'], 0)} der Experimente, mit Bonferroni-Schwelle in "
        f"{C.fmt_pct(here['winner_bonferroni'], 0)}; in einer Wiederholung bestätigt er sich in "
        f"{C.fmt_pct(here['confirmed'], 0)}."
    )
else:
    st.error(
        f"Ohne jede Wirkung misst die beste von {here['k']} Varianten im Mittel **{C.fmt_pp(here['mean_winner'])}**, ist in "
        f"**{C.fmt_pct(here['winner_sig'], 0)}** der Experimente „signifikant“ (mit Bonferroni-Schwelle "
        f"{C.fmt_pct(here['winner_bonferroni'], 0)}), und eine Wiederholung bestätigt sie nur in "
        f"{C.fmt_pct(here['confirmed'], 0)}. Der Gewinner ist ein Zufallstreffer."
    )

# --- Grenzen ---------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Zahl der Vergleiche steht vorher fest** | Wer Varianten nachträglich auswählt oder Kennzahlen erst nach dem Blick in die Daten wählt, hat mehr Vergleiche gemacht, als er zählt. | (dieses Stück) |
| **Eine Korrektur reicht** | Sie schützt die Fehlalarmrate, nicht die Schätzung: der Gewinner bleibt überschätzt. | (dieses Stück) |
| **Man blickt nur einmal** | Mehrere Blicke je Variante vervielfachen die Zahl der Tests. | Zwischenblicke und dauerndes Hinsehen |
| **Die Tests sind unabhängig oder positiv abhängig** | Benjamini-Hochberg ist für unabhängige oder positiv abhängige Statistiken bewiesen; bei beliebiger Abhängigkeit braucht es die strengere Variante. | (nicht Teil der Linie) |
| **Einheiten unabhängig und gleichartig** | Verhältniskennzahlen und Cluster vergrößern die Streuung jedes einzelnen Vergleichs. | Verhältniskennzahlen und Cluster |
| **Es gibt keine Streuung der echten Effekte** | Hier haben alle echten Varianten dieselbe Wirkung; wirken sie unterschiedlich, ist die Auswahl teilweise berechtigt. | Bandit statt A/B |
"""
)
st.caption(
    "Die Zahlen stammen aus dem erfundenen Vehikel dieses Stücks mit unabhängigen Fenstern. Die Bayes'sche Sicht "
    "(Schrumpfung der Schätzungen) und Subgruppen-Analysen sind nicht Teil der Demo."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Familienweise Fehlerrate.** Bei $m_0$ wirkungslosen Varianten und unabhängigen Tests zum Niveau $\alpha$ ist
$P(\text{mindestens ein Fehlalarm}) = 1 - (1 - \alpha)^{m_0}$; bei $m_0 = 20$ sind das 64,2 %. Bei gemeinsamer Kontrolle sind die
Tests positiv abhängig, die Rate liegt darunter.

**Bonferroni.** Lehne ab, wenn $p_i < \alpha/m$. Garantiert $\mathrm{FWER} \le \alpha$.

**Holm (1979).** Sortiere $p_{(1)} \le \dots \le p_{(m)}$; lehne der Reihe nach ab, solange $p_{(i)} < \alpha/(m - i + 1)$.
Dieselbe Garantie, nie weniger Entdeckungen als Bonferroni.

**Benjamini-Hochberg (1995).** Sei $i^*$ das größte $i$ mit $p_{(i)} \le \alpha\, i/m$; lehne alle $p_{(1)}, \dots, p_{(i^*)}$
ab. Garantiert $E[\text{falsche Entdeckungen} / \text{Entdeckungen}] \le \alpha\, m_0/m$ bei unabhängigen (oder positiv
abhängigen) Statistiken.

**Gewinnerfluch.** Für $k$ Schätzungen $\hat\Delta_j = \Delta + \varepsilon_j$ mit unabhängigem Rauschen ist
$E[\max_j \hat\Delta_j] = \Delta + E[\max_j \varepsilon_j] > \Delta$; der Aufschlag wächst mit $k$ und mit der Streuung. Die
Wiederholungsmessung der gekürten Variante ist dagegen unverzerrt.

Implementiert in `mtc_multiple.py` (Korrekturen), `mtc_evaluation.py` (Experimente, Gewinnerfluch), `mtc_stats.py` (Welch),
`mtc_vehicle.py` (Standort-Fenster), `generate_precomputed.py` (Pools).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html)."
)
