"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort-Fenster) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # Dispersion der negativ-binomialen Tagesnachfrage (ganzzahlig: Gamma(5) = Summe von 5 Exponentialzahlen)
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor dem Auswertefenster (gleiche Regel wie im Fenster)
WINDOW_DAYS = 28          # Auswertefenster: vier Wochen = ein "Standort-Fenster" = eine Einheit des Experiments
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A

Z_MIN, Z_MAX, DEFAULT_Z = 1.0, 2.0, 1.4      # echte Wirkung der "guten" Varianten (1,0 = keine Wirkung)
Z_STEP = 0.1
Z_GRID = tuple(round(Z_MIN + i * Z_STEP, 1) for i in range(int(round((Z_MAX - Z_MIN) / Z_STEP)) + 1))
POOL_SIZE = 10000         # Einheiten je Pool (je Sicherheitsfaktor)
ALPHA = 0.05

# Stück 5: viele Vergleiche
M_MIN, M_MAX, DEFAULT_M = 2, 50, 20                 # Zahl der Varianten (Vergleiche gegen Regel A)
M1_MIN, M1_MAX, DEFAULT_M1 = 0, 20, 2               # davon mit echter Wirkung
N_MIN, N_MAX, DEFAULT_N, N_STEP = 10, 100, 30, 5    # Fenster je Arm und Vergleich
SHARED_LABELS = ("Eine gemeinsame Kontrolle A für alle", "Eine eigene Kontrolle je Vergleich")
SEED_MAX, DEFAULT_SEED = 999999, 52          # Seed 52: das Einzelexperiment zeigt die typische Lage (ein Fehlalarm ohne Korrektur)
LIVE_REPS = 1000          # Wiederholungen der Live-Auswertung (aus dem Pool gezogen)
K_CURVE = (1, 2, 3, 5, 10, 20, 30, 50)    # Zahl der Varianten in der Gewinnerfluch-Kurve

METHODS = ("none", "bonferroni", "holm", "bh")
METHOD_LABELS = {"none": "Ohne Korrektur", "bonferroni": "Bonferroni", "holm": "Holm", "bh": "Benjamini-Hochberg"}
METHOD_COLORS = {"none": "#c0392b", "bonferroni": "#4c78a8", "holm": "#2F6B65", "bh": "#d95f02"}

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"

PRESETS = {
    "Zwanzig Vergleiche, zwei echte (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "m": DEFAULT_M, "m1": DEFAULT_M1,
                                                        "shared": 0, "seed": DEFAULT_SEED},
    "Zwanzig Vergleiche, kein echter Effekt": {"z": 1.0, "n": DEFAULT_N, "m": DEFAULT_M, "m1": 0, "shared": 0, "seed": DEFAULT_SEED},
    "Eigene Kontrolle je Vergleich": {"z": DEFAULT_Z, "n": DEFAULT_N, "m": DEFAULT_M, "m1": 2, "shared": 1, "seed": DEFAULT_SEED},
    "Viele echte, kleine Effekte": {"z": 1.2, "n": 50, "m": 40, "m1": 10, "shared": 0, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Zwanzig Vergleiche, zwei echte (Voreinstellung)": "20 Varianten gegen Regel A, 2 mit echter Wirkung (Sicherheitsfaktor 1,4), 30 Fenster je Arm, gemeinsame Kontrolle.",
    "Zwanzig Vergleiche, kein echter Effekt": "Keine Variante wirkt: jede Meldung ist ein Fehlalarm; ohne Korrektur kommt fast immer mindestens einer.",
    "Eigene Kontrolle je Vergleich": "Jeder Vergleich hat seine eigene Kontrollgruppe: die Tests sind unabhängig, die Fehlalarme addieren sich voll.",
    "Viele echte, kleine Effekte": "40 Varianten, 10 mit kleiner echter Wirkung (1,2): hier unterscheiden sich die Korrekturen in der Teststärke.",
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
