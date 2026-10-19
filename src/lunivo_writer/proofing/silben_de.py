"""Deutsche Sprechsilben — für „Silben farbig“ (Lesehilfe für Legasthenie).

Das sind keine Trennstellen für den Zeilenumbruch, sondern die Silben, wie man sie beim Sprechen und in der Schule klatscht:
Wan-de-rung, A-bend, Fens-ter, Ba-cken, Hand-schuh, Kar-tof-fel.

Vorgehen:
  1. Wortbausteine und Wortgrenzen in Zusammensetzungen (Sprech|stun|de, Zahn|arzt) kommen aus den Trennmustern von pyphen
     (nur als Hinweis; Stellen, die ein Stück ohne Vokal hinterlassen, werden verworfen).
  2. Innerhalb jedes Stücks gelten die Regeln der Sprechsilben: jede Silbe hat genau einen Vokalkern (ei, au, eu, äu, ie, aa/ee/oo
     zählen als ein Kern, a-o, i-o, e-u … als zwei); von mehreren Konsonanten zwischen zwei Kernen geht der letzte in die nächste Silbe,
     ch, sch, ck, ph, th, ß, qu bleiben zusammen, und Mitlaut + l/r (pl, br, tr …) beginnen gemeinsam eine Silbe.
Grenzen: Fremd- und Fachwörter, Eigennamen und Zusammensetzungen, die pyphen nicht kennt, können falsch geteilt werden (siehe tests).
"""
from __future__ import annotations

import re
from functools import lru_cache

VOKALE = set("aeiouäöüy")
DIPHTHONGE = ("ei", "ai", "ey", "ay", "au", "eu", "äu", "ou")
LANGE = ("aa", "ee", "oo", "ie")
EINHEITEN = ("sch", "ch", "ck", "ph", "th", "qu", "ß")
ONSET_PAARE = {"pl", "bl", "kl", "gl", "fl", "pr", "br", "tr", "dr", "kr", "gr", "fr", "tw"}      # Mitlaut + l/r beginnen eine Silbe
# -ie am Wortende wird getrennt gesprochen (Fa-mi-li-e), wenn es nicht betont ist
IE_GETRENNT = {"familie", "linie", "lilie", "folie", "serie", "studie", "prämie", "materie", "furie", "pinie", "kastanie",
               "bakterie", "arie", "orchidee"}
_NUR_BUCHSTABEN = re.compile(r"^[^\W\d_]+$", re.UNICODE)


def _einheiten(w: str) -> list[str]:
    """Zerlegt in Buchstabeneinheiten: Vokalkerne (V…), Konsonanteneinheiten (K…). → Liste von (art, text)."""
    out, i, n = [], 0, len(w)
    while i < n:
        z2, z3 = w[i:i + 2], w[i:i + 3]
        if z3 == "sch":
            out.append(("K", "sch")); i += 3; continue
        if z2 == "qu":
            out.append(("K", "qu")); i += 2; continue
        if z2 in ("ch", "ck", "ph", "th"):
            out.append(("K", z2)); i += 2; continue
        if w[i] == "ß":
            out.append(("K", "ß")); i += 1; continue
        if w[i] in VOKALE:
            if z2 in DIPHTHONGE or z2 in LANGE:
                out.append(("V", z2)); i += 2; continue
            out.append(("V", w[i])); i += 1; continue
        out.append(("K", w[i])); i += 1
    return out


def _wortende(w: str) -> list[int]:
    """Zusätzliche Grenzen am Wortende für getrennt gesprochene Vokale: Ide-en, Mu-se-um, Fami-li-en, Fa-mi-li-e."""
    n = len(w)
    if n > 4 and w.endswith("een"):
        return [n - 2]
    if n > 4 and w.endswith("eum"):
        return [n - 2]
    if n > 4 and w.endswith("ien"):
        return [n - 2]
    if w in IE_GETRENNT and w.endswith("ie"):
        return [n - 1]
    return []


def _stueck(w: str) -> list[int]:
    """Silbengrenzen (Indizes in w) innerhalb eines Wortstücks nach den Regeln der Sprechsilben."""
    ein = _einheiten(w)
    # Indizes der Einheiten im Wort
    pos, p = [], 0
    for _a, t in ein:
        pos.append(p)
        p += len(t)
    kerne = [i for i, (a, _t) in enumerate(ein) if a == "V"]
    grenzen = []
    for a, b in zip(kerne, kerne[1:]):
        dazwischen = ein[a + 1:b]
        if not dazwischen:                                             # Vokal | Vokal (Mu-se-um, Ak-ti-on)
            grenzen.append(pos[b])
            continue
        # Konsonanten zwischen zwei Kernen: der letzte (mit l/r davor: beide) beginnt die nächste Silbe
        k = len(dazwischen)
        onset = 1
        if k >= 2 and (dazwischen[-2][1][-1:] + dazwischen[-1][1]) in ONSET_PAARE and dazwischen[-2][1] not in ("sch", "ch"):
            onset = 2
        if k >= 2 and dazwischen[-1][1] in ("l", "r", "m", "n", "w") and dazwischen[-2][1] == "sch":
            onset = 2                                                  # schl, schm, schn, schr, schw
        if k >= 3 and dazwischen[-1][1] == "r" and dazwischen[-3][1] + dazwischen[-2][1] in ("sp", "st"):
            onset = 3                                                  # spr, str (Stra-ße, Kon-struk-ti-on bleibt unberührt)
        if k >= 2 and dazwischen[-1][1] == "h" and False:
            onset = 1
        grenzen.append(pos[b - onset])
    return grenzen


@lru_cache(maxsize=4)
def _pyphen():
    try:
        import pyphen
        return pyphen.Pyphen(lang="de_DE", left=2, right=2)
    except Exception:                                                  # noqa: BLE001 — ohne pyphen gelten nur die Regeln
        return None


def _hat_kern(s: str) -> bool:
    return any(c in VOKALE for c in s.lower())


def _hinweis_ok(w: str, p: int) -> bool:
    """Ist die von pyphen vorgeschlagene Stelle p ein Wortbaustein-Rand und keine bloße Zeilenumbruch-Stelle?
    pyphen setzt auch Stellen wie Ta-sta-tur oder fa-r-ben (gut für den Zeilenumbruch, falsch als Sprechsilbe): ein kurzer
    einzelner Vokal vor einer Konsonantenhäufung gehört nicht allein in eine Silbe (Ausnahme: unbetontes e wie in Ge-spenst)."""
    if not (_hat_kern(w[:p]) and _hat_kern(w[p:])):
        return False
    if w[p - 1] in VOKALE:
        k = 0
        for a, _t in _einheiten(w[p:]):
            if a == "V":
                break
            k += 1
        letzter = [t for a, t in _einheiten(w[:p]) if a == "V"][-1]
        if k >= 2 and len(letzter) == 1 and letzter != "e":
            return False
    return True


@lru_cache(maxsize=50000)
def silben(wort: str) -> tuple[str, ...]:
    """Das Wort in Sprechsilben. Wörter mit Ziffern/Sonderzeichen und ganz in Großbuchstaben bleiben ungeteilt."""
    if not _NUR_BUCHSTABEN.match(wort) or len(wort) < 2:
        return (wort,)
    w = wort.lower()
    stuecke, von = [], 0
    py = _pyphen()
    if py is not None:
        for p in py.positions(wort):                                   # Hinweise auf Wortgrenzen und Wortbausteine
            if _hat_kern(w[von:p]) and _hinweis_ok(w, p):
                stuecke.append((von, p))
                von = p
    stuecke.append((von, len(w)))
    grenzen = []
    for a, b in stuecke:
        grenzen.append(a)
        grenzen.extend(a + g for g in _stueck(w[a:b]))
    grenzen.extend(_wortende(w))
    grenzen = sorted({g for g in grenzen if 0 < g < len(w)})
    teile, von = [], 0
    for g in grenzen:
        teile.append(wort[von:g])
        von = g
    teile.append(wort[von:])
    return tuple(t for t in teile if t)
