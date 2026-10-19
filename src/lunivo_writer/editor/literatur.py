"""Quellen und Zitierweisen (APA, Harvard, IEEE, Chicago, DIN ISO 690)."""
from __future__ import annotations

ZITIERWEISEN = ["APA", "Harvard", "IEEE", "Chicago", "DIN ISO 690"]
TYPEN = ["Buch", "Aufsatz", "Webseite", "Bericht", "Sonstiges"]


def _nachname(autor: str) -> str:
    a = (autor or "").split(";")[0].strip()
    return a.split(",")[0].strip() if "," in a else (a.split()[-1] if a else "")


def _autoren(autor: str) -> str:
    teile = [t.strip() for t in (autor or "").split(";") if t.strip()]
    return " & ".join(teile) if len(teile) <= 2 else teile[0] + " et al."


def zitat(q: dict, weise: str, nr: int = 1) -> str:
    n, j = _nachname(q.get("autor", "")) or q.get("titel", "?"), q.get("jahr", "o. J.") or "o. J."
    if weise == "IEEE":
        return f"[{nr}]"
    if weise == "Harvard":
        return f"({n} {j})"
    if weise == "Chicago":
        return f"({n} {j})"
    if weise == "DIN ISO 690":
        return f"({n}, {j})"
    return f"({n}, {j})"


def eintrag(q: dict, weise: str, nr: int = 1) -> str:
    a, t, j = _autoren(q.get("autor", "")), q.get("titel", ""), q.get("jahr", "o. J.") or "o. J."
    v, o, u = q.get("verlag", ""), q.get("ort", ""), q.get("url", "")
    ort_verlag = ", ".join(x for x in (o, v) if x)
    if weise == "IEEE":
        s = f"[{nr}] {a}, „{t}“" + (f", {ort_verlag}" if ort_verlag else "") + f", {j}."
    elif weise == "Harvard":
        s = f"{a} ({j}) {t}." + (f" {ort_verlag}." if ort_verlag else "")
    elif weise == "Chicago":
        s = f"{a}. {j}. {t}." + (f" {ort_verlag}." if ort_verlag else "")
    elif weise == "DIN ISO 690":
        s = f"{a}: {t}." + (f" {ort_verlag}," if ort_verlag else "") + f" {j}."
    else:
        s = f"{a} ({j}). {t}." + (f" {ort_verlag}." if ort_verlag else "")
    if u:
        s += f" {u}"
    return " ".join(s.split())


def literaturverzeichnis(quellen: list[dict], weise: str) -> list[str]:
    ordnung = quellen if weise == "IEEE" else sorted(quellen, key=lambda q: _nachname(q.get("autor", "")).casefold())
    return [eintrag(q, weise, i) for i, q in enumerate(ordnung, start=1)]
