"""Das Fenster „Layout“ (ui/baukasten/layout_dialog.py) mit einem Bild verbinden: Werte vom Bild lesen, die Wahl auf das Bild anwenden.

Zwei Arten von Bildern gibt es im Editor:

* **frei** — liegt an einer Stelle des Blattes, hinter oder vor dem Text (siehe editor/freie_bilder.py). Sein Layout sind Lage, Größe, Drehung
  und die Schicht.
* **im Text** — steht in der Zeile oder wird links/rechts vom Text umflossen (editor/umbruch.py).

Die Umbruchart wechselt zwischen beiden: „Hinter/Vor dem Text“ macht ein Bild frei, jede andere Art setzt es in den Text zurück. Der Baustein
selbst kennt davon nichts; diese Datei ist die einzige Stelle, die Werte und Bild kennt.
"""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QTextCursor, QTextDocument, QTextImageFormat

from lunivo_writer.editor import freie_bilder as FB
from lunivo_writer.editor import umbruch as U
from lunivo_writer.models.page import mm_to_px, px_to_mm

from lunivo_writer.core.farben import Farbe
AUSR_H = {"left": "links", "center": "zentriert", "right": "rechts"}
AUSR_V = {"top": "oben", "center": "zentriert", "bottom": "unten"}
UMGEKEHRT_H = {v: k for k, v in AUSR_H.items()}
UMGEKEHRT_V = {v: k for k, v in AUSR_V.items()}


# ---- Ziel: das markierte Bild ---------------------------------------------------------------------------------------------
def ziel(ed):
    """(„frei“, Schlüssel, Angabe, Bild) oder („text“, Cursor) für das markierte Bild; sonst None."""
    sel = getattr(ed, "_frei_sel", None)
    if sel is not None:
        for key, a, bild, r, hinten, n in ed._frei_liste():
            if key == sel:
                return ("frei", key, a, bild)
    c = ed._bild_cursor()
    if c is not None:
        return ("text", c)
    return None


# ---- Lesen -----------------------------------------------------------------------------------------------------------------
def _achse_lesen(a: dict, waagerecht: bool, seite_mm: float) -> dict:
    ausr, off = a.get("ah" if waagerecht else "av") or "", float(a.get("xh" if waagerecht else "yv", 0.0))
    bezug = a.get("bh" if waagerecht else "bv", "spalte" if waagerecht else "absatz")
    w = {"modus": "abs", "mm": px_to_mm(off), "bezug_abs": bezug}
    if waagerecht and ausr in ("inside", "outside"):
        w.update(modus="buch", buch="innen" if ausr == "inside" else "aussen", bezug_buch="rand" if bezug == "rand" else "seite")
    elif ausr:
        w.update(modus="ausr", ausr=(AUSR_H if waagerecht else AUSR_V).get(ausr, "links"), bezug_ausr=bezug)
    return w


def lesen(ed, z) -> dict:
    from lunivo_writer.ui.baukasten.layout_dialog import STANDARD
    import copy
    w = copy.deepcopy(STANDARD)
    page = ed.page
    if z[0] == "frei":
        _k, key, a, bild = z
        w["umbruch"] = "hinter" if a.get("hinter") else "vor"
        w["h"].update(_achse_lesen(a, True, page.width_mm)); w["v"].update(_achse_lesen(a, False, page.height_mm))
        w["breite"].update(modus="abs", mm=px_to_mm(a["b"])); w["hoehe"].update(modus="abs", mm=px_to_mm(a["h"]))
        w["drehung"] = float(a.get("dreh", 0.0))
        w["mit_text"], w["ueberlappen"], w["verankern"] = bool(a.get("mit_text", False)), bool(a.get("ueberlappen", True)), bool(a.get("verankern", False))
        w["original"] = (px_to_mm(bild.width()), px_to_mm(bild.height()))
        return w
    c = z[1]
    f = c.charFormat().toImageFormat()
    seite = U.schwebend(ed.document(), c.selectionStart())
    w["umbruch"] = "quadrat" if seite else "textfluss"
    if seite:
        w["zeilen"] = "links" if seite == "rechts" else "rechts"
    img = ed.document().resource(QTextDocument.ImageResource, QUrl(f.name()))
    ob, oh = (img.width(), img.height()) if isinstance(img, QImage) and not img.isNull() else (f.width() or 100, f.height() or 100)
    w["breite"].update(mm=px_to_mm(f.width() or ob)); w["hoehe"].update(mm=px_to_mm(f.height() or oh)); w["original"] = (px_to_mm(ob), px_to_mm(oh))
    return w


# ---- Anwenden --------------------------------------------------------------------------------------------------------------
def _box(page, bezug: str, waagerecht: bool) -> float:
    if bezug == "seite":
        return mm_to_px(page.width_mm if waagerecht else page.height_mm)
    return page.content_width_px if waagerecht else page.content_height_px


def _achse_schreiben(a: dict, w: dict, page, waagerecht: bool) -> None:
    ak, ok_ = ("ah", "xh") if waagerecht else ("av", "yv")
    bk = "bh" if waagerecht else "bv"
    if w["modus"] == "ausr":
        a[ak] = (UMGEKEHRT_H if waagerecht else UMGEKEHRT_V).get(w["ausr"], ""); a[ok_] = 0.0; a[bk] = w["bezug_ausr"]
    elif w["modus"] == "buch":
        a[ak] = "inside" if w.get("buch") == "innen" else "outside"; a[ok_] = 0.0; a[bk] = w.get("bezug_buch", "rand")
    elif w["modus"] == "rel":
        a[ak] = ""; a[bk] = w["bezug_rel"]; a[ok_] = _box(page, w["bezug_rel"], waagerecht) * w["proz"] / 100.0
    else:
        a[ak] = ""; a[ok_] = mm_to_px(w["mm"]); a[bk] = w["bezug_abs"]


def _mass(w: dict, page, waagerecht: bool, alt: float) -> float:
    if w["modus"] == "rel":
        return _box(page, w["bezug"], waagerecht) * w["proz"] / 100.0
    return mm_to_px(w["mm"]) if w["mm"] > 0 else alt


def anwenden(ed, z, werte: dict) -> None:
    """Schreibt die Wahl des Fensters (oder eines Teils davon: nur die genannten Schlüssel) auf das Bild."""
    alt = lesen(ed, z)
    w = dict(alt)
    for k, v in werte.items():
        w[k] = {**alt[k], **v} if isinstance(v, dict) and isinstance(alt.get(k), dict) else v
    art = w["umbruch"]
    if z[0] == "frei":
        _k, key, a, bild = z
        if art in ("hinter", "vor"):
            neu = dict(a)
            neu["hinter"] = art == "hinter"
            _achse_schreiben(neu, w["h"], ed.page, True); _achse_schreiben(neu, w["v"], ed.page, False)
            neu["b"] = _mass(w["breite"], ed.page, True, a["b"]); neu["h"] = _mass(w["hoehe"], ed.page, False, a["h"])
            neu["dreh"] = float(w["drehung"])
            neu["mit_text"], neu["ueberlappen"], neu["verankern"] = bool(w["mit_text"]), bool(w["ueberlappen"]), bool(w["verankern"])
            _speichern_frei(ed, key, neu)
        elif key[0] == "t":                                       # frei → in den Text zurück
            _frei_zu_text(ed, key, a, bild, w)
        return
    c = z[1]
    if art in ("hinter", "vor"):
        _text_zu_frei(ed, c, w, art == "hinter")
        return
    f = QTextImageFormat(c.charFormat().toImageFormat())
    f.setWidth(mm_to_px(w["breite"]["mm"])); f.setHeight(mm_to_px(w["hoehe"]["mm"]))
    c.mergeCharFormat(f)
    modus = {"textfluss": "zeile", "obenunten": "oben_unten"}.get(art)
    if modus is None:                                              # Quadrat, Passend, Transparent: das Bild steht links oder rechts, der Text läuft daneben
        modus = "links" if w["zeilen"] == "rechts" else "rechts"
    U.umbruch_setzen(ed, modus)


def _speichern_frei(ed, key, neu: dict) -> None:
    sauber = FB.ohne_hilfsangaben(neu)
    if key[0] == "k":
        for a in ed.page.bilder:
            if id(a) == key[1]:
                a.update(sauber)
        ed.document().setModified(True)
        ed.pageApplied.emit()
    else:
        ed._frei_absatz_aendern(key[1], key[2], sauber)
    ed._frei_rev = None
    ed.viewport().update()


def _text_zu_frei(ed, c, w: dict, hinter: bool) -> None:
    """Ein Bild im Text wird frei: es verlässt die Zeile und liegt, wo der Absatz beginnt (dort lässt es sich ziehen)."""
    doc = ed.document()
    pos = c.selectionStart()
    f = c.charFormat().toImageFormat()
    img = doc.resource(QTextDocument.ImageResource, QUrl(f.name()))
    if not isinstance(img, QImage) or img.isNull():
        return
    c0 = QTextCursor(doc); c0.beginEditBlock()
    if U.schwebend(doc, pos):
        pos = U.schwebend_entfernen(doc, pos)
    else:
        c.removeSelectedText()
    name = FB.neuer_name(doc)
    doc.addResource(QTextDocument.ImageResource, QUrl(name), img)
    a = {"n": name, "b": mm_to_px(w["breite"]["mm"]), "h": mm_to_px(w["hoehe"]["mm"]), "bh": "spalte", "xh": 0.0, "bv": "absatz", "yv": 0.0,
         "ah": "", "av": "", "hinter": hinter, "ellipse": False, "dreh": float(w["drehung"])}
    _achse_schreiben(a, w["h"], ed.page, True); _achse_schreiben(a, w["v"], ed.page, False)
    FB.an_absatz(QTextCursor(doc.findBlock(pos)), a)
    c0.endEditBlock()
    ed._frei_rev = None
    ed.viewport().update()


def _frei_zu_text(ed, key, a: dict, bild: QImage, w: dict) -> None:
    """Ein freies Bild kommt in den Text: es steht am Anfang seines Absatzes (in der Zeile, links/rechts umflossen oder allein)."""
    doc = ed.document()
    b = doc.findBlockByNumber(key[1])
    if not b.isValid():
        return
    c0 = QTextCursor(doc); c0.beginEditBlock()
    ed._frei_absatz_aendern(key[1], key[2], None)
    name = f"bild-{id(bild)}"
    doc.addResource(QTextDocument.ImageResource, QUrl(name), bild)
    f = QTextImageFormat(); f.setName(name); f.setWidth(a["b"]); f.setHeight(a["h"])
    c = QTextCursor(doc.findBlock(b.position())); c.insertImage(f)
    c0.endEditBlock()
    sel = QTextCursor(doc); sel.setPosition(b.position()); sel.setPosition(b.position() + 1, QTextCursor.KeepAnchor)
    ed.setTextCursor(sel)
    ed._frei_sel = None
    anwenden(ed, ("text", ed._bild_cursor()), {"umbruch": w["umbruch"], "zeilen": w["zeilen"]})


# ---- Füllung und Kontur ---------------------------------------------------------------------------------------------------
FX_SCHLUESSEL = ("schatten", "reflektion", "leuchten", "weich")


def format_lesen(ed, z) -> dict | None:
    """Füllung, Kontur und Effekte des markierten freien Bildes im Format des Panels (``ObjektFormatPanel``); sonst None."""
    if z is None or z[0] != "frei":
        return None
    a = z[2]
    w = {"fuell": a.get("fuell"), "rand": a.get("rand")}
    w.update({k: dict(v) for k, v in (a.get("fx") or {}).items() if k in FX_SCHLUESSEL})
    return w


def format_aus_panel(ed, z, werte: dict) -> bool:
    """Wendet die Werte des Panels an: Füllung, Kontur und alle Effekte (fehlende Effekte sind ausgeschaltet)."""
    if z is None or z[0] != "frei":
        return False
    fuell = werte.get("fuell")
    if fuell and fuell.get("art") == "bild" and fuell.get("unveraendert"):
        fuell = (z[2].get("fuell") if (z[2].get("fuell") or {}).get("art") == "bild" else "__nicht__")       # das vorhandene Bild behalten
    return format_setzen(ed, z, fuell=fuell, rand=werte.get("rand"), fx={k: v for k, v in werte.items() if k in FX_SCHLUESSEL})


def format_setzen(ed, z, fuell="__nicht__", rand="__nicht__", rand_teil: dict | None = None, fx="__nicht__") -> bool:
    """Füllung (``fuell``: Wörterbuch oder None) und/oder Kontur (``rand``: Wörterbuch oder None; ``rand_teil`` ändert nur einzelne Angaben der
    vorhandenen Kontur) des markierten freien Bildes. → True, wenn etwas gesetzt wurde."""
    if z is None or z[0] != "frei":
        return False
    _k, key, a, _bild = z
    neu = dict(a)
    if fuell != "__nicht__":
        neu["fuell"] = fuell
    if rand != "__nicht__":
        neu["rand"] = rand
    if fx != "__nicht__":
        if fx:
            neu["fx"] = fx
        else:
            neu.pop("fx", None)
    if rand_teil:
        alt = dict(neu.get("rand") or {"b": 2.0, "farbe": Farbe.SCHWARZ, "art": "einfach"})
        alt.update(rand_teil)
        neu["rand"] = alt
    _speichern_frei(ed, key, neu)
    return True


def fuellbild_setzen(ed, z, bild: QImage) -> bool:
    """„Füllung ▸ Bild“: das Bild als Füllung; im Text liegt es als Ressource des Dokuments, in der Kopfzeile am Bild selbst."""
    if z is None or z[0] != "frei" or bild.isNull():
        return False
    key = z[1]
    if key[0] == "k":
        return format_setzen(ed, z, fuell={"art": "bild", "bild": bild})
    name = FB.neuer_name(ed.document())
    ed.document().addResource(QTextDocument.ImageResource, QUrl(name), bild)
    return format_setzen(ed, z, fuell={"art": "bild", "n": name})


# ---- Zeichentools: Ausrichten, Drehen, Ebene, Maße, Format übertragen -------------------------------------------------------------
AUSRICHTEN = {"links": ("ah", "left"), "mitte": ("ah", "center"), "rechts": ("ah", "right"),
              "oben": ("av", "top"), "mittig": ("av", "center"), "unten": ("av", "bottom")}


def frei_aendern(ed, z, **teile) -> bool:
    """Einzelne Angaben des markierten freien Bildes ersetzen (Schlüssel der Angabe: ``dreh``, ``hinter`` …)."""
    if z is None or z[0] != "frei":
        return False
    _speichern_frei(ed, z[1], {**z[2], **teile})
    return True


def ausrichten(ed, z, wie: str) -> bool:
    """Das freie Bild am Blatt ausrichten (links/mitte/rechts, oben/mittig/unten)."""
    if wie not in AUSRICHTEN or z is None or z[0] != "frei":
        return False
    achse, wert = AUSRICHTEN[wie]
    bezug = ("bh", "xh") if achse == "ah" else ("bv", "yv")
    return frei_aendern(ed, z, **{achse: wert, bezug[0]: "seite", bezug[1]: 0.0})


def drehen(ed, z, grad: float) -> bool:
    if z is None or z[0] != "frei":
        return False
    return frei_aendern(ed, z, dreh=(float(z[2].get("dreh", 0.0)) + grad) % 360.0)


def ebene(ed, z, vorn: bool) -> bool:
    """„Eine Ebene nach vorne/hinten“: das Bild liegt vor oder hinter dem Text (frei positioniert)."""
    if z is None:
        return False
    if z[0] == "frei":
        return frei_aendern(ed, z, hinter=not vorn)
    anwenden(ed, z, {"umbruch": "vor" if vorn else "hinter"})
    return True


def masse_lesen(ed, z) -> tuple[float, float] | None:
    """Breite und Höhe des markierten Bildes in mm."""
    if z is None:
        return None
    if z[0] == "frei":
        return px_to_mm(float(z[2]["b"])), px_to_mm(float(z[2]["h"]))
    f = z[1].charFormat().toImageFormat()
    return px_to_mm(f.width()), px_to_mm(f.height())


def masse_setzen(ed, z, breite_mm: float | None = None, hoehe_mm: float | None = None) -> bool:
    if z is None:
        return False
    if z[0] == "frei":
        return frei_aendern(ed, z, **({"b": mm_to_px(breite_mm)} if breite_mm else {}), **({"h": mm_to_px(hoehe_mm)} if hoehe_mm else {}))
    anwenden(ed, z, {**({"breite": {"mm": breite_mm}} if breite_mm else {}), **({"hoehe": {"mm": hoehe_mm}} if hoehe_mm else {})})
    return True


def format_merken(z) -> dict | None:
    """Füllung, Kontur und Effekte des markierten freien Bildes zum „Format übertragen“."""
    if z is None or z[0] != "frei":
        return None
    a = z[2]
    return {k: a[k] for k in ("fuell", "rand", "fx") if a.get(k)} | {"_leer": [k for k in ("fuell", "rand", "fx") if not a.get(k)]}


def format_uebertragen(ed, z, merk: dict) -> bool:
    if z is None or z[0] != "frei" or not merk:
        return False
    neu = dict(z[2])
    for k in merk.get("_leer", ()):
        neu.pop(k, None)
    neu.update({k: v for k, v in merk.items() if k != "_leer"})
    _speichern_frei(ed, z[1], neu)
    return True
