"""Reiter Schreibhilfe (und Prüfen): Dokumentprüfung, KI, Lesen, Vorlesen."""
import threading

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk  # noqa: E402

from . import befehl, hilfen
from .. import einstellungen, html_io, schreibhilfe


def _d(w):
    return w.dok()


@befehl("tafel_zeigen")
def _tafel(w, _=None):
    w.seitenleiste.set_visible(not w.seitenleiste.get_visible())
    w.band_auffrischen()


@befehl("pruefen")
def _pruefen(w, _=None):
    d = w.dok()
    if not d:
        return
    w.seitenleiste.set_visible(True)
    text = d.text()
    w.status("Prüfe …")
    w.schreibhilfe.pruef_knopf.set_sensitive(False)

    def arbeit():
        try:
            funde = schreibhilfe.pruefen(text)
            GLib.idle_add(_fertig, w, d, text, funde, None)
        except Exception as e:
            GLib.idle_add(_fertig, w, d, text, [], str(e))
    threading.Thread(target=arbeit, daemon=True).start()


def _fertig(w, d, text, funde, fehler):
    w.schreibhilfe.pruef_knopf.set_sensitive(True)
    if d.text() != text:
        return w.status("Der Text hat sich geändert – bitte noch einmal prüfen.")
    if fehler:
        w.status("Die Prüfung ist fehlgeschlagen.")
        return w.meldung("Prüfung fehlgeschlagen", fehler)
    w.schreibhilfe.zeigen(d, funde)
    w.status("%d Funde." % len(funde) if funde else "Nichts gefunden.")


from .. import kichat


# ================================================================ Lesen
LESEFARBEN = {"Weiß": "#FFFFFF", "Creme": "#FFF8E1", "Hellgelb": "#FFFBCC", "Hellblau": "#E8F1FA",
              "Hellgrün": "#E9F5EC", "Rosa": "#FDEBEB", "Grau": "#EEEEEE"}


def lesehilfe_anwenden(w, d):
    """Wendet die Leseeinstellungen auf die Ansicht an (nur Darstellung, nicht Dokumentinhalt)."""
    l = w.werte.setdefault("lesehilfe", {})
    tag = html_io.tag_holen(d.puffer, "grund")
    if l.get("schrift"):
        d.vorgabe_schrift = l["schrift"]
        tag.set_property("family", l["schrift"])
    if l.get("groesse"):
        d.vorgabe_groesse = l["groesse"]
        tag.set_property("size-points", float(l["groesse"]))
    if l.get("zeilenabstand"):
        tag.set_property("line-height", float(l["zeilenabstand"]))
    if l.get("buchstabenabstand") is not None:
        tag.set_property("letter-spacing", int(float(l["buchstabenabstand"]) * 1024))
    if l.get("hintergrund"):
        d.seite_setzen(seitenfarbe=l["hintergrund"])
    d.puffer.apply_tag(tag, d.puffer.get_start_iter(), d.puffer.get_end_iter())


@befehl("lesehilfe")
def _lesehilfe(w, _=None):
    d = _d(w)
    if not d:
        return
    l = w.werte.setdefault("lesehilfe", {"schrift": d.vorgabe_schrift, "groesse": d.vorgabe_groesse,
                                         "zeilenabstand": 1.5, "buchstabenabstand": 0.5, "hintergrund": "#FFF8E1"})
    dlg = Gtk.Window(transient_for=w, modal=True, title="Lesehilfe")
    dlg.set_default_size(440, -1)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(16)
    dlg.set_child(box)
    box.append(Gtk.Label(label="Was das Lesen leichter macht. Das betrifft nur die Darstellung am Bildschirm.", xalign=0, wrap=True))
    felder = {}

    def zeile(name, widget):
        z = Gtk.Box(spacing=8)
        lb = Gtk.Label(label=name, xalign=0)
        lb.set_size_request(150, -1)
        z.append(lb)
        z.append(widget)
        box.append(z)
    fam = Gtk.DropDown.new_from_strings(w.familien)
    if l.get("schrift") in w.familien:
        fam.set_selected(w.familien.index(l["schrift"]))
    felder["schrift"] = fam
    zeile("Schriftart", fam)
    gr = Gtk.SpinButton.new_with_range(8, 48, 1)
    gr.set_value(float(l.get("groesse", 12)))
    zeile("Schriftgröße", gr)
    za = Gtk.SpinButton.new_with_range(1.0, 3.0, 0.1)
    za.set_digits(1)
    za.set_value(float(l.get("zeilenabstand", 1.5)))
    zeile("Zeilenabstand", za)
    ba = Gtk.SpinButton.new_with_range(0.0, 4.0, 0.25)
    ba.set_digits(2)
    ba.set_value(float(l.get("buchstabenabstand", 0.5)))
    zeile("Buchstabenabstand (pt)", ba)
    hg = Gtk.DropDown.new_from_strings(list(LESEFARBEN))
    for i, (n, f) in enumerate(LESEFARBEN.items()):
        if f == l.get("hintergrund"):
            hg.set_selected(i)
    zeile("Blattfarbe", hg)
    ok = Gtk.Button(label="Übernehmen")
    ok.add_css_class("suggested-action")

    def los(*_):
        l.update({"schrift": w.familien[fam.get_selected()], "groesse": gr.get_value(),
                  "zeilenabstand": za.get_value(), "buchstabenabstand": ba.get_value(),
                  "hintergrund": list(LESEFARBEN.values())[hg.get_selected()]})
        for x in w.alle_dokumente():
            lesehilfe_anwenden(w, x)
        dlg.close()
    ok.connect("clicked", los)
    box.append(ok)
    dlg.present()


@befehl("schrift_zum_lesen")
def _schrift_zum_lesen(w, _=None):
    _lesehilfe(w)


@befehl("zeilenfokus")
def _zeilenfokus(w, _=None):
    an = w.schalten("zeilenfokus")
    for d in w.alle_dokumente():
        _fokus_verdrahten(d)
        d.fokus_an = an
        _fokus_aktualisieren(d)
    w.status("Zeilenfokus %s." % ("ein" if an else "aus"))


def _fokus_verdrahten(d):
    if getattr(d, "_fokus_verdrahtet", False):
        return
    d._fokus_verdrahtet = True
    d.puffer.connect("notify::cursor-position", lambda *_: _fokus_aktualisieren(d))


def _fokus_aktualisieren(d):
    tag = html_io.tag_holen(d.puffer, "dimm")
    d.puffer.remove_tag(tag, d.puffer.get_start_iter(), d.puffer.get_end_iter())
    if not getattr(d, "fokus_an", False):
        return
    zeile = d.puffer.get_iter_at_mark(d.puffer.get_insert()).get_line()
    _, a = d.puffer.get_iter_at_line(zeile)
    b = a.copy()
    if not b.ends_line():
        b.forward_to_line_end()
    d.puffer.apply_tag(tag, d.puffer.get_start_iter(), a)
    b.forward_char()
    d.puffer.apply_tag(tag, b, d.puffer.get_end_iter())


@befehl("lesemodus")
def _lesemodus(w, _=None):
    an = w.schalten("lesemodus")
    for d in w.alle_dokumente():
        d.ansicht.set_editable(not an)
        d.ansicht.set_cursor_visible(not an)
        d.zoom_setzen(130 if an else 100)
    w.band.stapel.set_visible(not an)
    w.zeile_oben.set_visible(not an)
    w.seitenleiste.set_visible(not an and w.werte.get("schreibhilfe", True))
    w.status("Lesemodus – zum Beenden noch einmal Schreibhilfe ▸ Lesemodus (oder Esc).")
    if an:
        _esc = Gtk.EventControllerKey()
        _esc.connect("key-pressed", lambda c, k, kc, s: (_lesemodus(w), True)[1] if k == Gdk.KEY_Escape and w.zustand("lesemodus") else False)
        w.add_controller(_esc)


# ================================================================ Beim Schreiben
@befehl("vorhersage")
def _vorhersage(w, _=None):
    an = w.schalten("vorhersage")
    for d in w.alle_dokumente():
        d.vorhersage_an = an
        if not an:
            d._vorhersage_verbergen()
    w.status("Wortvorhersage %s (Tab übernimmt den ersten Vorschlag)." % ("ein" if an else "aus"))


@befehl("autokorrektur")
def _autokorr(w, _=None):
    an = w.schalten("autokorrektur")
    for d in w.alle_dokumente():
        d.autokorrektur_an = an
    w.status("AutoKorrektur %s (Anführungszeichen „“, –, …, ©, Satzanfang)." % ("ein" if an else "aus"))


# ================================================================ Vorlesen
def _sprechen(w, text):
    import shutil
    import subprocess
    if not shutil.which("spd-say"):
        return w.meldung("Vorlesen", "spd-say (Sprachausgabe) ist nicht installiert (sudo apt install speech-dispatcher).")
    v = w.werte.setdefault("stimme", {"sprache": "de", "tempo": 0})
    subprocess.run(["spd-say", "-C"], capture_output=True)
    subprocess.Popen(["spd-say", "-l", v.get("sprache", "de"), "-r", str(v.get("tempo", 0)), "-w", text[:20000]],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    w.status("Wird vorgelesen …")


@befehl("vorlesen")
def _vorlesen(w, _=None):
    d = _d(w)
    if d:
        text, sel = d.auswahl_oder_alles()
        _sprechen(w, text.replace("￼", " "))


@befehl("vorlesen_ab_satz")
def _vorlesen_ab(w, _=None):
    d = _d(w)
    if d:
        it = d.puffer.get_iter_at_mark(d.puffer.get_insert())
        _sprechen(w, d.puffer.get_slice(it, d.puffer.get_end_iter(), True).replace("￼", " "))


@befehl("vorlesen_stopp")
def _vorlesen_stopp(w, _=None):
    import subprocess
    subprocess.run(["spd-say", "-C"], capture_output=True)
    w.status("Vorlesen angehalten.")


@befehl("stimme_waehlen")
def _stimme(w, _=None):
    v = w.werte.setdefault("stimme", {"sprache": "de", "tempo": 0})

    def ok(x):
        v["sprache"] = x[0].strip() or "de"
        v["tempo"] = max(-100, min(100, int(hilfen.zahl(x[1], 0))))
        w.status("Stimme: %s, Tempo %d" % (v["sprache"], v["tempo"]))
    hilfen.frage(w, "Stimme und Tempo", [("Sprache (de, en, …)", v["sprache"]), ("Tempo (−100 … +100)", v["tempo"])], ok,
                 "Die Sprachausgabe läuft über Speech Dispatcher.")


# ================================================================ Sprache
@befehl("optionen_sprache")
def _optionen_sprache(w, _=None):
    from . import ueberpruefen
    ueberpruefen._pruefsprache(w)


# ================================================================ KI
def _anbieter(w):
    a = schreibhilfe.anbieter_aktiv(w.werte)
    if not a.get("modell"):
        _ki_konfig(w)
        return None
    return a


def _ki_lauf(w, anweisung, titel, text=None, ersetzbar=True):
    d = _d(w)
    if not d:
        return
    a = _anbieter(w)
    if a is None:
        return
    text, sel = (text, None) if text is not None else d.auswahl_oder_alles()
    text = text.replace("￼", "")
    if not text.strip():
        return w.status("Kein Text.")
    ziel, wozu = w.schreibhilfe.zielgruppe()
    if ziel != "egal" or wozu:
        anweisung += "\nDer Text ist für: %s.%s" % (ziel, (" Worum es geht: " + wozu) if wozu else "")
    bereich = (sel[0].get_offset(), sel[1].get_offset()) if sel else (0, len(d.text()))
    ausgang = d.text()
    w.status("KI arbeitet … (das kann etwas dauern)")

    def arbeit():
        try:
            erg = schreibhilfe.chat(a, [{"role": "system", "content": anweisung}, {"role": "user", "content": text}])
            GLib.idle_add(_ki_fertig, w, d, titel, bereich, ausgang, erg, None, ersetzbar)
        except Exception as e:
            GLib.idle_add(_ki_fertig, w, d, titel, bereich, ausgang, "", str(e), ersetzbar)
    threading.Thread(target=arbeit, daemon=True).start()


def _ki_fertig(w, d, titel, bereich, ausgang, ergebnis, fehler, ersetzbar):
    if fehler:
        w.status("KI fehlgeschlagen.")
        return w.meldung("KI nicht erreichbar", fehler)
    dlg = Gtk.AlertDialog()
    dlg.set_message(titel)
    dlg.set_detail(ergebnis[:1800])
    dlg.set_buttons(["Verwerfen", "Als neuen Reiter", "Ersetzen"] if ersetzbar else ["Schließen", "Als neuen Reiter"])
    dlg.set_cancel_button(0)

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n == 2 and ersetzbar and d.text() == ausgang:
            d.bereich_ersetzen(bereich[0], bereich[1], ergebnis)
        elif n == 1:
            neu = w.neu()
            neu.puffer.set_text(ergebnis)
    dlg.choose(w, None, fertig)
    w.status("KI fertig.")


@befehl("ki_korrektur")
def _ki_korr(w, _=None):
    _ki_lauf(w, schreibhilfe.ANWEISUNGEN["korrektur"], "Korrigierter Text")


@befehl("ki_vorschlaege")
def _ki_vor(w, _=None):
    _ki_lauf(w, "Du bist ein Lektor. Nenne 3 bis 5 konkrete Verbesserungsvorschläge für Verständlichkeit und Stil des deutschen Textes, "
                "je Vorschlag eine Zeile. Schreibe den Text nicht um.", "Vorschläge", ersetzbar=False)


@befehl("ki_uebersetzen")
def _ki_uebers(w, _=None):
    _ki_lauf(w, schreibhilfe.ANWEISUNGEN["englisch"], "Übersetzung")


@befehl("ki_kurz")
def _ki_kurz(w, _=None):
    _ki_lauf(w, schreibhilfe.ANWEISUNGEN["kurz"], "Zusammenfassung")


@befehl("chat_umschalten")
def _chat(w, _=None):
    if getattr(w, "ki_chat", None) is None:
        w.ki_chat = kichat.KiChat(w)
        w.tafeln.append(w.ki_chat)
        w.ki_chat.set_visible(False)
    w.ki_chat.set_visible(not w.ki_chat.get_visible())
    if w.ki_chat.get_visible():
        w.ki_chat.eingabe.grab_focus()


@befehl("ki_konfiguration")
def _ki_konfig(w, _=None):
    liste = schreibhilfe.anbieter_liste(w.werte)
    dlg = Gtk.Window(transient_for=w, modal=True, title="KI-Konfiguration")
    dlg.set_default_size(520, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(14)
    dlg.set_child(box)
    box.append(Gtk.Label(label="KI-Anbieter. Ollama läuft auf diesem Rechner; andere Anbieter brauchen eine Internetverbindung.", xalign=0, wrap=True))
    namen = Gtk.DropDown.new_from_strings([a["name"] for a in liste])
    namen.set_selected(min(int(w.werte.get("anbieter_aktiv", 0)), len(liste) - 1))
    box.append(namen)
    felder = {}
    for k, t in (("name", "Name"), ("url", "Adresse"), ("modell", "Modell"), ("schluessel", "Schlüssel (nur bei Online-Anbietern)")):
        z = Gtk.Box(spacing=8)
        lb = Gtk.Label(label=t, xalign=0)
        lb.set_size_request(170, -1)
        z.append(lb)
        e = Gtk.Entry(hexpand=True, visibility=(k != "schluessel"))
        felder[k] = e
        z.append(e)
        box.append(z)
    typ = Gtk.DropDown.new_from_strings(["Ollama", "OpenAI-kompatibel"])
    z = Gtk.Box(spacing=8)
    lb = Gtk.Label(label="Art", xalign=0)
    lb.set_size_request(170, -1)
    z.append(lb)
    z.append(typ)
    box.append(z)
    modelle = Gtk.DropDown.new_from_strings(["(Modelle abfragen)"])
    box.append(modelle)

    def laden(*_):
        a = liste[namen.get_selected()]
        for k, e in felder.items():
            e.set_text(a.get(k, ""))
        typ.set_selected(0 if a.get("typ", "ollama") == "ollama" else 1)
    namen.connect("notify::selected", laden)
    laden()

    def abfragen(*_):
        a = dict(liste[namen.get_selected()])
        a.update({k: e.get_text() for k, e in felder.items()})
        a["typ"] = "ollama" if typ.get_selected() == 0 else "openai"
        try:
            m = schreibhilfe.modelle_von(a)
        except Exception as e:
            return w.meldung("Anbieter nicht erreichbar", str(e))
        modelle.set_model(Gtk.StringList.new(m or ["(keine)"]))
        if felder["modell"].get_text() in m:
            modelle.set_selected(m.index(felder["modell"].get_text()))
        modelle.connect("notify::selected", lambda *_: felder["modell"].set_text(m[modelle.get_selected()]) if m else None)
        w.status("%d Modelle gefunden." % len(m))
    ab = Gtk.Button(label="Modelle abfragen")
    ab.connect("clicked", abfragen)
    box.append(ab)
    ok = Gtk.Button(label="Speichern und verwenden")
    ok.add_css_class("suggested-action")

    def speichern(*_):
        i = namen.get_selected()
        a = liste[i]
        a.update({k: e.get_text().strip() for k, e in felder.items()})
        a["typ"] = "ollama" if typ.get_selected() == 0 else "openai"
        w.werte["anbieter_aktiv"] = i
        w.status("KI: %s – %s" % (a["name"], a["modell"] or "kein Modell"))
        dlg.close()
    ok.connect("clicked", speichern)
    box.append(ok)
    dlg.present()


@befehl("anbieter_hinzufuegen")
def _anbieter_neu(w, _=None):
    liste = schreibhilfe.anbieter_liste(w.werte)

    def ok(v):
        if not v[0].strip() or not v[1].strip():
            return
        liste.append({"name": v[0].strip(), "typ": "openai", "url": v[1].strip(), "modell": v[2].strip(), "schluessel": v[3].strip()})
        w.werte["anbieter_aktiv"] = len(liste) - 1
        w.status("Anbieter „%s“ hinzugefügt und ausgewählt." % v[0])
    hilfen.frage(w, "Eigenen Anbieter hinzufügen", [("Name", ""), ("Adresse (…/v1)", "https://"), ("Modell", ""), ("Schlüssel", "")], ok,
                 "Für jeden Dienst mit OpenAI-kompatibler Schnittstelle.")


@befehl("assistent_erstellen")
def _assistent(w, _=None):
    def ok(v):
        if not v[0].strip() or not v[1].strip():
            return
        w.werte.setdefault("assistenten", []).append({"name": v[0].strip(), "anweisung": v[1].strip()})
        w.status("Assistent „%s“ erstellt (Schreibhilfe ▸ Assistenten)." % v[0])
    hilfen.frage(w, "Eigenen Assistenten erstellen", [("Name", ""), ("Anweisung", "Du schreibst …")], ok,
                 "Der Assistent bearbeitet die Auswahl (oder den ganzen Text) nach Ihrer Anweisung.")


@befehl("assistenten")
def _assistenten(w, _=None):
    liste = w.werte.get("assistenten", [])
    if not liste:
        return w.meldung("Assistenten", "Noch kein eigener Assistent (Schreibhilfe ▸ Eigenen Assistenten erstellen).")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Assistent wählen")
    dlg.set_buttons([a["name"] for a in liste[:6]] + ["Abbrechen"])
    dlg.set_cancel_button(len(liste[:6]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(liste[:6]):
            _ki_lauf(w, liste[n]["anweisung"], liste[n]["name"])
    dlg.choose(w, None, fertig)


@befehl("welche_hilfe")
def _welche(w, _=None):
    w.meldung("Welche Hilfe wann", "Prüfen: findet Regelverstöße, die ein Rechtschreibprüfer nicht findet (doppelte Wörter, "
              "Leerzeichen, Zeichensetzung).\nGründlich prüfen: dazu die Rechtschreibung mit Wörterbuch.\n"
              "KI-Korrektur: korrigiert den Text mit der KI.\nVorschläge: Hinweise zum Stil, ohne etwas zu ändern.\n"
              "Zusammenfassen / Nach Englisch: arbeiten mit der KI auf dem ausgewählten Text.")


# ================================================================ Bausteine
def _bausteine(w):
    return w.werte.setdefault("bausteine", [{"name": "Gruß", "text": "Mit freundlichen Grüßen"},
                                           {"name": "Anrede", "text": "Sehr geehrte Damen und Herren,"}])


@befehl("schnellbaustein")
def _schnellbaustein(w, _=None):
    d = _d(w)
    b = _bausteine(w)
    if not d or not b:
        return w.meldung("Textbausteine", "Es gibt noch keine Bausteine.")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Baustein einfügen")
    dlg.set_buttons([x["name"] for x in b[:7]] + ["Abbrechen"])
    dlg.set_cancel_button(len(b[:7]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(b[:7]):
            d.text_einfuegen(b[n]["text"])
    dlg.choose(w, None, fertig)


@befehl("textbaustein")
def _textbaustein(w, _=None):
    _schnellbaustein(w)


@befehl("textbausteine")
def _textbausteine(w, _=None):
    liste = _bausteine(w)
    dlg = Gtk.Window(transient_for=w, modal=True, title="Textbausteine")
    dlg.set_default_size(520, 420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(12)
    dlg.set_child(box)
    lb = Gtk.ListBox()
    rolle = Gtk.ScrolledWindow(vexpand=True)
    rolle.set_child(lb)
    box.append(rolle)

    def fuellen():
        k = lb.get_first_child()
        while k:
            n = k.get_next_sibling()
            lb.remove(k)
            k = n
        for x in liste:
            lb.append(Gtk.Label(label="%s — %s" % (x["name"], x["text"][:60].replace("\n", " ")), xalign=0))
    fuellen()
    z = Gtk.Box(spacing=6)
    neu = Gtk.Button(label="Neu …")
    neu.connect("clicked", lambda *_: hilfen.frage(w, "Neuer Baustein", [("Name", ""), ("Text", "")],
                                                   lambda v: (liste.append({"name": v[0], "text": v[1]}), fuellen())))
    weg = Gtk.Button(label="Löschen")
    weg.connect("clicked", lambda *_: (lb.get_selected_row() and liste.pop(lb.get_selected_row().get_index()), fuellen()))
    z.append(neu)
    z.append(weg)
    box.append(z)
    dlg.present()
