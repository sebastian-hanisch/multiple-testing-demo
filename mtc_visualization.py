"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import mtc_constants as C

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=380, legend=dict(orientation="h", y=-0.25))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_sorted_p(p, real, alpha=C.ALPHA):
    """Die p-Werte der Größe nach geordnet mit den Schwellen der Verfahren. Rot: Variante ohne echte Wirkung."""
    m = len(p)
    order = np.argsort(p)
    ranks = np.arange(1, m + 1)
    ps = np.asarray(p)[order]
    is_real = np.asarray(real)[order]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, m], y=[alpha, alpha], mode="lines", name="ohne Korrektur (0,05)",
                             line=dict(color=C.METHOD_COLORS["none"], width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=[1, m], y=[alpha / m, alpha / m], mode="lines", name="Bonferroni (0,05 / m)",
                             line=dict(color=C.METHOD_COLORS["bonferroni"], width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=list(ranks), y=[alpha / (m - i + 1) for i in ranks], mode="lines", name="Holm (0,05 / (m − i + 1))",
                             line=dict(color=C.METHOD_COLORS["holm"], width=2), line_shape="hv"))
    fig.add_trace(go.Scatter(x=list(ranks), y=[alpha * i / m for i in ranks], mode="lines", name="Benjamini-Hochberg (0,05 · i / m)",
                             line=dict(color=C.METHOD_COLORS["bh"], width=2, dash="dashdot")))
    for flag, name, color in ((True, "echte Wirkung", C.COLOR_B), (False, "keine Wirkung", C.COLOR_MISS)):
        mask = is_real == flag
        if mask.any():
            fig.add_trace(go.Scatter(x=list(ranks[mask]), y=list(ps[mask]), mode="markers", name=name,
                                     marker=dict(color=color, size=9, line=dict(color="white", width=1))))
    fig.update_yaxes(type="log", range=[-5, 0.1])
    fig.update_xaxes(range=[0.5, m + 0.5])
    return _finish(fig, "p-Werte der Größe nach geordnet, mit den Schwellen der Verfahren", "Rang (kleinster p-Wert zuerst)",
                   "p-Wert (logarithmisch)")


def build_rates(rows, has_real):
    """Gruppierte Säulen: familienweise Fehlerrate, Rate falscher Entdeckungen und Teststärke je Verfahren, in %."""
    fig = go.Figure()
    groups = [("fwer", "Mindestens ein Fehlalarm"), ("fdr", "Anteil falscher Entdeckungen")]
    if has_real:
        groups.append(("power", "Teststärke je echter Variante"))
    for method in C.METHODS:
        fig.add_trace(go.Bar(x=[g[1] for g in groups], y=[100 * rows[method][g[0]] for g in groups], name=C.METHOD_LABELS[method],
                             marker_color=C.METHOD_COLORS[method]))
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="5 %", annotation_position="top right")
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, 100])
    return _finish(fig, "Was die Verfahren halten", None, "Anteil der Experimente in %", height=340)


def build_winner(points, truth, k_now):
    """Mittlere Schätzung der gekürten Variante gegen die Zahl der Varianten; waagerecht die wahre Wirkung (Punkte)."""
    ks = [p["k"] for p in points]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=[100 * p["mean_winner"] for p in points], mode="lines+markers", name="beste Variante",
                             line=dict(color=C.COLOR_B, width=3)))
    fig.add_trace(go.Scatter(x=ks, y=[100 * truth] * len(ks), mode="lines", name="wahre Wirkung",
                             line=dict(color=C.COLOR_TRUTH, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=ks, y=[100 * p["mean_replication"] for p in points], mode="lines+markers",
                             name="dieselbe Variante, frisch gemessen", line=dict(color=C.COLOR_A, width=2, dash="dot")))
    if k_now in ks:
        i = ks.index(k_now)
        fig.add_trace(go.Scatter(x=[k_now], y=[100 * points[i]["mean_winner"]], mode="markers", name="Ihre Wahl",
                                 marker=dict(color=C.COLOR_MISS, size=14, symbol="diamond")))
    fig.update_xaxes(type="log")
    return _finish(fig, "Die beste von k gleich guten Varianten: was gemessen wird, was sie wirklich kann", "Zahl der Varianten k",
                   "Wirkung in Prozentpunkten Servicegrad")
