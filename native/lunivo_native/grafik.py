"""Vektorgrafiken als SVG-Text: Formen, Diagramme, SmartArt, WordArt, Formeln, Piktogramme."""
import html
import math
import re

from . import symbole

PALETTE = ["#2F6FB5", "#D08A3E", "#3E9C7A", "#C27BA0", "#8E7CC3", "#E06666", "#76A5AF", "#F1C232"]


def _kopf(b, h):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'font-family="Georgia, serif">' % (b, h, b, h))


def _t(s):
    return html.escape(str(s))


# ------------------------------------------------------------------ Formen
FORMEN = [
    "Rechteck", "Abgerundetes Rechteck", "Ellipse", "Dreieck", "Raute", "Sechseck", "Pfeil rechts", "Pfeil links",
    "Doppelpfeil", "Stern", "Herz", "Sprechblase", "Linie", "Wolke",
]


def form(name, fuell="#2F6FB5", rand="#1B4A80", breite=160, hoehe=100, text=""):
    b, h = breite, hoehe
    stil = 'fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"' % (fuell, rand)
    s = _kopf(b, h)
    m = 4
    if name == "Rechteck":
        k = '<rect x="%d" y="%d" width="%d" height="%d" %s/>' % (m, m, b - 2 * m, h - 2 * m, stil)
    elif name == "Abgerundetes Rechteck":
        k = '<rect x="%d" y="%d" width="%d" height="%d" rx="18" %s/>' % (m, m, b - 2 * m, h - 2 * m, stil)
    elif name == "Ellipse":
        k = '<ellipse cx="%g" cy="%g" rx="%g" ry="%g" %s/>' % (b / 2, h / 2, b / 2 - m, h / 2 - m, stil)
    elif name == "Dreieck":
        k = '<polygon points="%g,%d %d,%d %d,%d" %s/>' % (b / 2, m, b - m, h - m, m, h - m, stil)
    elif name == "Raute":
        k = '<polygon points="%g,%d %d,%g %g,%d %d,%g" %s/>' % (b / 2, m, b - m, h / 2, b / 2, h - m, m, h / 2, stil)
    elif name == "Sechseck":
        k = '<polygon points="%g,%d %g,%d %d,%g %g,%d %g,%d %d,%g" %s/>' % (
            b * .25, m, b * .75, m, b - m, h / 2, b * .75, h - m, b * .25, h - m, m, h / 2, stil)
    elif name in ("Pfeil rechts", "Pfeil links", "Doppelpfeil"):
        t0, t1 = h * .3, h * .7
        if name == "Pfeil rechts":
            pts = [(m, t0), (b * .6, t0), (b * .6, m), (b - m, h / 2), (b * .6, h - m), (b * .6, t1), (m, t1)]
        elif name == "Pfeil links":
            pts = [(b - m, t0), (b * .4, t0), (b * .4, m), (m, h / 2), (b * .4, h - m), (b * .4, t1), (b - m, t1)]
        else:
            pts = [(m, h / 2), (b * .22, m), (b * .22, t0), (b * .78, t0), (b * .78, m), (b - m, h / 2),
                   (b * .78, h - m), (b * .78, t1), (b * .22, t1), (b * .22, h - m)]
        k = '<polygon points="%s" %s/>' % (" ".join("%g,%g" % p for p in pts), stil)
    elif name == "Stern":
        cx, cy, R, r = b / 2, h / 2, min(b, h) / 2 - m, min(b, h) / 5
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rad = R if i % 2 == 0 else r
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        k = '<polygon points="%s" %s/>' % (" ".join("%g,%g" % p for p in pts), stil)
    elif name == "Herz":
        k = ('<path d="M%g,%g C%g,%g %g,%g %g,%g C%g,%g %g,%g %g,%g C%g,%g %g,%g %g,%g Z" %s/>' % (
            b / 2, h * .9, b * .05, h * .6, b * .05, h * .1, b / 2, h * .28,
            b * .95, h * .1, b * .95, h * .6, b / 2, h * .9, b / 2, h * .9, b / 2, h * .9, b / 2, h * .9, stil))
    elif name == "Sprechblase":
        k = ('<path d="M%d,%d H%d V%g H%g L%g,%d L%g,%g H%d Z" %s/>' % (
            m, m, b - m, h * .7, b * .45, b * .3, h - m, b * .3, h * .7, m, stil))
    elif name == "Linie":
        k = '<line x1="%d" y1="%g" x2="%d" y2="%g" stroke="%s" stroke-width="4" stroke-linecap="round"/>' % (m, h / 2, b - m, h / 2, rand)
    elif name == "Wolke":
        k = ('<path d="M%g,%g a%g,%g 0 0 1 %g,%g a%g,%g 0 0 1 %g,%g a%g,%g 0 0 1 %g,%g H%g a%g,%g 0 0 1 0,-%g Z" %s/>' % (
            b * .25, h * .75, h * .22, h * .22, h * .05, -h * .4, h * .3, h * .3, h * .45, -h * .1,
            h * .22, h * .22, b * .1, h * .3, b * .25, h * .12, h * .12, h * .24, stil))
    else:
        k = ""
    if text:
        k += '<text x="%g" y="%g" text-anchor="middle" dominant-baseline="middle" font-size="18" fill="#FFFFFF">%s</text>' % (
            b / 2, h / 2, _t(text))
    return s + k + "</svg>"


# ------------------------------------------------------------------ Diagramme
def diagramm(art, kopf, zeilen, titel="", breite=460, hoehe=280):
    """art: saeulen|balken|linie|kreis; kopf: ['Reihe1', …]; zeilen: [['Kategorie', 1.0, …]]"""
    s = _kopf(breite, hoehe)
    s += '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (breite, hoehe)
    if titel:
        s += '<text x="%g" y="22" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">%s</text>' % (breite / 2, _t(titel))
    daten = [[z[0]] + [float(v) for v in z[1:]] for z in zeilen]
    n_reihen = len(kopf)
    x0, y0, x1, y1 = 54, 40, breite - 16, hoehe - 52
    if art == "kreis":
        werte = [max(d[1], 0) for d in daten]
        summe = sum(werte) or 1
        cx, cy, r = (x0 + x1) / 2 - 60, (y0 + y1) / 2, min(x1 - x0, y1 - y0) / 2 - 6
        w = -math.pi / 2
        for i, v in enumerate(werte):
            a = 2 * math.pi * v / summe
            xa, ya, xb, yb = cx + r * math.cos(w), cy + r * math.sin(w), cx + r * math.cos(w + a), cy + r * math.sin(w + a)
            gross = 1 if a > math.pi else 0
            if len(werte) == 1:
                s += '<circle cx="%g" cy="%g" r="%g" fill="%s"/>' % (cx, cy, r, PALETTE[0])
            else:
                s += '<path d="M%g,%g L%g,%g A%g,%g 0 %d 1 %g,%g Z" fill="%s" stroke="#fff" stroke-width="2"/>' % (
                    cx, cy, xa, ya, r, r, gross, xb, yb, PALETTE[i % len(PALETTE)])
            w += a
        for i, d in enumerate(daten):
            yy = y0 + 14 + i * 20
            s += '<rect x="%g" y="%g" width="12" height="12" fill="%s"/><text x="%g" y="%g" font-size="12" fill="#333">%s (%.3g)</text>' % (
                breite - 150, yy - 10, PALETTE[i % len(PALETTE)], breite - 132, yy, _t(d[0]), d[1])
        return s + "</svg>"
    maxw = max([abs(v) for d in daten for v in d[1:]] + [1e-9])
    schritt = 10 ** math.floor(math.log10(maxw))
    for f in (1, 2, 2.5, 5, 10):
        if maxw <= f * schritt:
            spitze = f * schritt
            break
    s += '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#888"/><line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#888"/>' % (
        x0, y0, x0, y1, x0, y1, x1, y1)
    for i in range(6):
        v = spitze * i / 5
        yy = y1 - (y1 - y0) * i / 5
        s += '<line x1="%d" y1="%g" x2="%d" y2="%g" stroke="#ddd"/><text x="%d" y="%g" text-anchor="end" font-size="11" fill="#555">%.3g</text>' % (
            x0, yy, x1, yy, x0 - 6, yy + 4, v)
    n = len(daten)
    breite_k = (x1 - x0) / max(n, 1)
    if art == "linie":
        for r in range(n_reihen):
            pts = " ".join("%g,%g" % (x0 + breite_k * (i + .5), y1 - (y1 - y0) * daten[i][r + 1] / spitze) for i in range(n))
            s += '<polyline points="%s" fill="none" stroke="%s" stroke-width="3"/>' % (pts, PALETTE[r % len(PALETTE)])
            for i in range(n):
                s += '<circle cx="%g" cy="%g" r="4" fill="%s"/>' % (x0 + breite_k * (i + .5), y1 - (y1 - y0) * daten[i][r + 1] / spitze, PALETTE[r % len(PALETTE)])
    else:
        bb = breite_k * 0.7 / max(n_reihen, 1)
        for i, d in enumerate(daten):
            for r in range(n_reihen):
                hh = (y1 - y0) * d[r + 1] / spitze
                s += '<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>' % (
                    x0 + breite_k * i + breite_k * .15 + bb * r, y1 - hh, bb, hh, PALETTE[r % len(PALETTE)])
    for i, d in enumerate(daten):
        s += '<text x="%g" y="%d" text-anchor="middle" font-size="11" fill="#333">%s</text>' % (x0 + breite_k * (i + .5), y1 + 16, _t(d[0]))
    if n_reihen > 1:
        for r, nm in enumerate(kopf):
            s += '<rect x="%g" y="%d" width="10" height="10" fill="%s"/><text x="%g" y="%d" font-size="11" fill="#333">%s</text>' % (
                x0 + r * 110, hoehe - 22, PALETTE[r % len(PALETTE)], x0 + r * 110 + 14, hoehe - 13, _t(nm))
    return s + "</svg>"


# ------------------------------------------------------------------ SmartArt
SMARTART = ["Liste", "Prozess", "Zyklus", "Hierarchie", "Pyramide", "Vergleich"]


def smartart(art, eintraege, breite=520, hoehe=220):
    n = max(len(eintraege), 1)
    s = _kopf(breite, hoehe) + '<rect width="%d" height="%d" fill="#FFFFFF"/>' % (breite, hoehe)

    def kasten(x, y, w, h, text, i):
        return ('<rect x="%g" y="%g" width="%g" height="%g" rx="8" fill="%s"/>'
                '<text x="%g" y="%g" text-anchor="middle" dominant-baseline="middle" font-size="14" fill="#fff">%s</text>' % (
                    x, y, w, h, PALETTE[i % len(PALETTE)], x + w / 2, y + h / 2, _t(text)))
    if art == "Liste":
        h = min(46, (hoehe - 20) / n - 8)
        for i, t in enumerate(eintraege):
            s += kasten(20, 10 + i * (h + 8), breite - 40, h, t, i)
    elif art == "Prozess":
        w = (breite - 40) / n - 22
        for i, t in enumerate(eintraege):
            x = 20 + i * (w + 22)
            s += kasten(x, hoehe / 2 - 32, w, 64, t, i)
            if i < n - 1:
                s += '<polygon points="%g,%g %g,%g %g,%g" fill="#888"/>' % (x + w + 4, hoehe / 2 - 9, x + w + 18, hoehe / 2, x + w + 4, hoehe / 2 + 9)
    elif art == "Zyklus":
        cx, cy, R = breite / 2, hoehe / 2, min(breite, hoehe) / 2 - 38
        for i, t in enumerate(eintraege):
            a = -math.pi / 2 + 2 * math.pi * i / n
            x, y = cx + R * 1.6 * math.cos(a), cy + R * math.sin(a)
            s += kasten(x - 55, y - 22, 110, 44, t, i)
        s += '<ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="none" stroke="#999" stroke-dasharray="5 4"/>' % (cx, cy, R * 1.6, R)
    elif art == "Hierarchie":
        s += kasten(breite / 2 - 70, 12, 140, 44, eintraege[0] if eintraege else "", 0)
        rest = eintraege[1:]
        m = max(len(rest), 1)
        w = (breite - 30) / m - 10
        for i, t in enumerate(rest):
            x = 15 + i * (w + 10)
            s += '<path d="M%g,56 V%g H%g V%g" stroke="#999" fill="none"/>' % (breite / 2, 90, x + w / 2, 120)
            s += kasten(x, 120, w, 44, t, i + 1)
    elif art == "Pyramide":
        h = (hoehe - 20) / n
        for i, t in enumerate(eintraege):
            top = 10 + i * h
            w1 = breite * .8 * i / n + 30
            w2 = breite * .8 * (i + 1) / n + 30
            cx = breite / 2
            s += '<polygon points="%g,%g %g,%g %g,%g %g,%g" fill="%s" stroke="#fff" stroke-width="2"/>' % (
                cx - w1 / 2, top, cx + w1 / 2, top, cx + w2 / 2, top + h, cx - w2 / 2, top + h, PALETTE[i % len(PALETTE)])
            s += '<text x="%g" y="%g" text-anchor="middle" dominant-baseline="middle" font-size="13" fill="#fff">%s</text>' % (cx, top + h / 2, _t(t))
    else:                                                   # Vergleich
        halb = (n + 1) // 2
        for i, t in enumerate(eintraege):
            sp = 0 if i < halb else 1
            zl = i if i < halb else i - halb
            s += kasten(20 + sp * (breite / 2), 12 + zl * 52, breite / 2 - 30, 44, t, sp)
    return s + "</svg>"


# ------------------------------------------------------------------ WordArt
WORTSTILE = {
    "Verlauf": ("#2F6FB5", "#C27BA0"),
    "Feuer": ("#E06666", "#F1C232"),
    "Natur": ("#3E9C7A", "#B6D7A8"),
    "Ozean": ("#1B4A80", "#76A5AF"),
    "Gold": ("#7F6000", "#FFD966"),
}


def wordart(text, stil="Verlauf", groesse=56, schatten=True):
    c1, c2 = WORTSTILE.get(stil, WORTSTILE["Verlauf"])
    breite = max(int(len(text) * groesse * 0.62) + 40, 120)
    hoehe = int(groesse * 1.5)
    s = _kopf(breite, hoehe)
    s += '<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>' % (c1, c2)
    if schatten:
        s += '<text x="%g" y="%g" text-anchor="middle" font-size="%d" font-weight="bold" fill="#00000040">%s</text>' % (
            breite / 2 + 3, hoehe * .72 + 3, groesse, _t(text))
    s += '<text x="%g" y="%g" text-anchor="middle" font-size="%d" font-weight="bold" fill="url(#g)" stroke="#222" stroke-width="1">%s</text>' % (
        breite / 2, hoehe * .72, groesse, _t(text))
    return s + "</svg>", breite, hoehe


# ------------------------------------------------------------------ Formel
_GRIECH = {"alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "theta": "θ", "lambda": "λ", "mu": "μ",
           "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "omega": "ω", "Delta": "Δ", "Sigma": "Σ",
           "Omega": "Ω", "infty": "∞", "cdot": "·", "times": "×", "pm": "±", "leq": "≤", "geq": "≥", "neq": "≠",
           "approx": "≈", "rightarrow": "→", "sum": "∑", "int": "∫", "partial": "∂", "nabla": "∇", "to": "→"}


def _formel_lesen(s):
    """Sehr kleine LaTeX-Teilmenge → Baum."""
    pos = [0]

    def gruppe():
        if pos[0] < len(s) and s[pos[0]] == "{":
            pos[0] += 1
            r = folge("}")
            pos[0] += 1
            return r
        if pos[0] < len(s):
            c = s[pos[0]]
            pos[0] += 1
            return [("t", c)]
        return []

    def folge(ende=None):
        knoten = []
        while pos[0] < len(s) and (ende is None or s[pos[0]] != ende):
            c = s[pos[0]]
            if c == "\\":
                pos[0] += 1
                m = re.match(r"[A-Za-z]+", s[pos[0]:])
                name = m.group(0) if m else ""
                pos[0] += len(name)
                if name == "frac":
                    a, b = gruppe(), gruppe()
                    knoten.append(("frac", a, b))
                elif name == "sqrt":
                    knoten.append(("sqrt", gruppe()))
                elif name in _GRIECH:
                    knoten.append(("t", _GRIECH[name]))
                else:
                    knoten.append(("t", name))
            elif c in "^_":
                pos[0] += 1
                knoten.append(("hoch" if c == "^" else "tief", gruppe()))
            elif c == "{":
                knoten.extend(gruppe())
            else:
                pos[0] += 1
                knoten.append(("t", c))
        return knoten
    return folge()


def _mass(knoten, fs):
    """→ (breite, höhe_über_grundlinie, tiefe_unter_grundlinie, svg-Funktion(x, y))"""
    teile = []
    x = 0.0
    ueber, unter = fs * 0.75, fs * 0.25
    for k in knoten:
        if k[0] == "t":
            w = fs * (0.62 if k[1].isalnum() or k[1] in "∑∫" else 0.5)
            if k[1] in "∑":
                w = fs * 0.9
            kursiv = ' font-style="italic"' if k[1].isalpha() and k[1].isascii() else ""
            teile.append((x, 0, '<text x="{x}" y="{y}" font-size="%g"%s>%s</text>' % (fs, kursiv, _t(k[1]))))
            x += w
        elif k[0] in ("hoch", "tief"):
            w, u, d, f = _mass(k[1], fs * 0.7)
            dy = -fs * 0.4 if k[0] == "hoch" else fs * 0.25
            teile.append((x, dy, f))
            ueber = max(ueber, u - dy)
            unter = max(unter, d + dy)
            x += w
        elif k[0] == "frac":
            w1, u1, d1, f1 = _mass(k[1], fs * 0.85)
            w2, u2, d2, f2 = _mass(k[2], fs * 0.85)
            w = max(w1, w2) + 6
            teile.append((x + (w - w1) / 2, -fs * 0.35 - d1, f1))
            teile.append((x + (w - w2) / 2, fs * 0.35 + u2, f2))
            teile.append((x, 0, '<line x1="{x}" y1="{y2}" x2="{x2}" y2="{y2}" stroke="#111" stroke-width="1.2"/>', w))
            ueber = max(ueber, fs * 0.35 + u1 + d1 + 0.0)
            unter = max(unter, fs * 0.35 + u2 + d2)
            x += w
        elif k[0] == "sqrt":
            w, u, d, f = _mass(k[1], fs)
            teile.append((x + fs * 0.5, 0, f))
            teile.append((x, 0, "SQRT", w + fs * 0.5, u))
            ueber = max(ueber, u + 4)
            x += w + fs * 0.5 + 2
    breite = x

    def zeichne(x0, y0):
        out = ""
        for t in teile:
            tx, dy, f = t[0], t[1], t[2]
            if callable(f):
                out += f(x0 + tx, y0 + dy)
            elif f == "SQRT":
                w, u = t[3], t[4]
                out += '<polyline points="%g,%g %g,%g %g,%g %g,%g %g,%g" fill="none" stroke="#111" stroke-width="1.3"/>' % (
                    x0 + tx, y0 - fs * 0.3, x0 + tx + fs * 0.15, y0 - fs * 0.05, x0 + tx + fs * 0.3, y0 - u - 2,
                    x0 + tx + w, y0 - u - 2, x0 + tx + w, y0 - u + 3)
            elif f.startswith("<line"):
                out += f.format(x=x0 + tx, x2=x0 + tx + t[3], y2=y0 + dy - fs * 0.3)
            else:
                out += f.format(x=x0 + tx, y=y0 + dy)
        return out
    return breite, ueber, unter, zeichne


def formel(text, groesse=26):
    baum = _formel_lesen(text)
    b, u, d, f = _mass(baum, groesse)
    breite, hoehe = int(b + 16), int(u + d + 14)
    svg = _kopf(breite, hoehe) + '<g fill="#111" font-family="Georgia, serif">' + f(8, u + 7) + "</g></svg>"
    return svg, breite, hoehe


# ------------------------------------------------------------------ Piktogramm
def piktogramm(name, farbe="#2F6FB5", groesse=64, strich=1.7):
    pfad = symbole._PFADE.get(name, "")
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 24 24" fill="none" '
            'stroke="%s" stroke-width="%g" stroke-linecap="round" stroke-linejoin="round"><path d="%s"/></svg>' % (
                groesse, groesse, farbe, strich, pfad)), groesse, groesse
