"""Datei-Menü: Neu, Öffnen, Speichern, Export, Drucken, Eigenschaften, Hilfe, Beenden."""
import os

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib  # noqa: E402

from . import befehl, hilfen
from .. import drucken as druck_modul, pfade

DATEIFILTER = [
    ("Alle Textdokumente", ["*.html", "*.htm", "*.docx", "*.doc", "*.odt", "*.ott", "*.rtf", "*.txt", "*.md"]),
    ("Word (docx, doc)", ["*.docx", "*.doc"]),
    ("OpenDocument (odt)", ["*.odt", "*.ott"]),
    ("HTML", ["*.html", "*.htm"]),
    ("Text", ["*.txt", "*.md"]),
]


def filterliste(eintraege):
    liste = Gio.ListStore.new(Gtk.FileFilter)
    for name, muster in eintraege:
        f = Gtk.FileFilter()
        f.set_name(name)
        for m in muster:
            f.add_pattern(m)
        liste.append(f)
    return liste


def _ordner_vorgeben(w, dlg):
    """„Speicherort für Dateien“ aus den Optionen: dort gehen Öffnen und Speichern auf."""
    o = w.werte.get("ordner_oeffnen")
    if o and os.path.isdir(o):
        dlg.set_initial_folder(Gio.File.new_for_path(o))


@befehl("neu")
def _neu(w, _=None):
    w.neu()


@befehl("oeffnen")
def _oeffnen(w, _=None):
    dlg = Gtk.FileDialog(title="Dokument öffnen")
    _ordner_vorgeben(w, dlg)
    dlg.set_filters(filterliste(DATEIFILTER))

    def fertig(dlg, res):
        try:
            dateien = dlg.open_multiple_finish(res)
        except GLib.Error:
            return
        for i in range(dateien.get_n_items()):
            w.datei_oeffnen(dateien.get_item(i).get_path())
    dlg.open_multiple(w, None, fertig)


@befehl("zuletzt_oeffnen")
def _zuletzt(w, _=None):
    liste = [p for p in w.werte.get("zuletzt", []) if os.path.exists(p)]
    if not liste:
        return w.meldung("Zuletzt geöffnet", "Es wurde noch nichts geöffnet.")
    dlg = Gtk.AlertDialog()
    dlg.set_message("Zuletzt geöffnet")
    dlg.set_buttons([os.path.basename(p) for p in liste[:6]] + ["Abbrechen"])
    dlg.set_cancel_button(len(liste[:6]))

    def fertig(dlg, res):
        try:
            n = dlg.choose_finish(res)
        except GLib.Error:
            return
        if n < len(liste[:6]):
            w.datei_oeffnen(liste[n])
    dlg.choose(w, None, fertig)


def vorlagen_ordner():
    xdg = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_TEMPLATES)
    return xdg or os.path.expanduser("~/Vorlagen")


@befehl("vorlagen_waehlen")
def _vorlagen_waehlen(w, _=None):
    ordner = vorlagen_ordner()
    dlg = Gtk.FileDialog(title="Neu aus Vorlage")
    if os.path.isdir(ordner):
        dlg.set_initial_folder(Gio.File.new_for_path(ordner))
    dlg.set_filters(filterliste(DATEIFILTER))

    def fertig(dlg, res):
        try:
            datei = dlg.open_finish(res)
        except GLib.Error:
            return
        d = w.datei_oeffnen(datei.get_path())
        if d:                                  # als neues, unbenanntes Dokument weiterarbeiten
            d.pfad = None
            d.titel = "Unbenannt (aus Vorlage)"
            d.puffer.set_modified(True)
            w._titel_auffrischen(d)
    dlg.open(w, None, fertig)


@befehl("vorlagen_ordner")
def _vorlagen_ordner(w, _=None):
    o = vorlagen_ordner()
    os.makedirs(o, exist_ok=True)
    Gtk.FileLauncher.new(Gio.File.new_for_path(o)).launch(w, None, None)


@befehl("speichern")
def _speichern(w, _=None):
    _speichern_dann(w, None)


@befehl("speichern_dann")
def _speichern_dann(w, weiter):
    d = w.dok()
    if not d:
        return
    if not d.pfad or os.path.splitext(d.pfad)[1].lower() not in (".html", ".htm", ".docx", ".odt", ".rtf"):
        return _speichern_unter(w, weiter)
    try:
        d.speichern(sicherungskopie=w.werte.get("sicherung_kopie", True))
        w.zuletzt_merken(d.pfad)
        w.status("Gespeichert: %s" % d.pfad)
    except Exception as e:
        return w.meldung("Speichern hat nicht geklappt", str(e))
    if callable(weiter):
        weiter()


@befehl("speichern_unter")
def _speichern_unter_b(w, _=None):
    _speichern_unter(w, None)


def _speichern_unter(w, weiter):
    d = w.dok()
    if not d:
        return
    dlg = Gtk.FileDialog(title="Speichern unter")
    dlg.set_initial_name(os.path.splitext(d.anzeigename())[0] + "." + w.werte.get("standardformat", "docx"))
    _ordner_vorgeben(w, dlg)
    dlg.set_filters(filterliste([("Word (docx)", ["*.docx"]), ("OpenDocument (odt)", ["*.odt"]),
                                 ("HTML", ["*.html"]), ("Text", ["*.txt"])]))

    def fertig(dlg, res):
        try:
            datei = dlg.save_finish(res)
        except GLib.Error:
            return
        pfad = datei.get_path()
        if not os.path.splitext(pfad)[1]:
            pfad += ".docx"
        try:
            d.speichern(pfad)
            w.zuletzt_merken(pfad)
            w.status("Gespeichert: %s" % pfad)
        except Exception as e:
            return w.meldung("Speichern hat nicht geklappt", str(e))
        w._titel_auffrischen(d)
        if callable(weiter):
            weiter()
    dlg.save(w, None, fertig)


def _exportieren(w, endung, name):
    import threading
    d = w.dok()
    if not d:
        return
    dlg = Gtk.FileDialog(title="Exportieren als " + name)
    dlg.set_initial_name(os.path.splitext(d.anzeigename())[0] + "." + endung)

    def fertig(dlg, res):
        try:
            datei = dlg.save_finish(res)
        except GLib.Error:
            return
        pfad = datei.get_path()
        if not pfad.lower().endswith("." + endung):
            pfad += "." + endung
        w.status("Exportiere …")

        def arbeit():
            try:
                d.speichern_unter(pfad)
                GLib.idle_add(w.status, "Exportiert: " + pfad)
            except Exception as e:
                GLib.idle_add(w.meldung, "Export fehlgeschlagen", str(e))
        threading.Thread(target=arbeit, daemon=True).start()
    dlg.save(w, None, fertig)


@befehl("speichern_pdf")
def _pdf(w, _=None):
    _exportieren(w, "pdf", "PDF-Dokument")


@befehl("exportieren")
def _export(w, art=None):
    _exportieren(w, art or "pdf", {"docx": "Word", "odt": "OpenDocument", "txt": "Text", "pdf": "PDF",
                                   "rtf": "RTF", "html": "HTML"}.get(art, art))


@befehl("drucken")
def _drucken(w, _=None):
    d = w.dok()
    if d:
        druck_modul.drucken(w, d)


@befehl("vorschau")
def _vorschau(w, _=None):
    d = w.dok()
    if d:
        druck_modul.drucken(w, d, Gtk.PrintOperationAction.PREVIEW)


@befehl("drucker_einrichten")
def _drucker(w, _=None):
    einst = Gtk.PrintSettings()
    gespeichert = w.werte.get("drucker_seite")
    seite = Gtk.PageSetup()
    Gtk.print_run_page_setup_dialog_async(w, seite, einst, lambda s, p: w.status("Seite eingerichtet."))


_VORSCHLAEGE = ["Büro", "Bearbeiter", "Layout", "Abteilung", "Referenz", "Verleger", "Projekt", "Status"]
_ZUS = ["Titel", "Betreff", "Autor", "Manager", "Firma", "Kategorie", "Stichwort"]


@befehl("eigenschaften")
def _eigenschaften(w, _=None):
    """Dokumenteigenschaften wie in der Vorlage: drei Reiter, Cancel/OK."""
    import time
    d = w.dok()
    if not d:
        return
    eig = d.meta.setdefault("eigenschaften", {})
    benutzer = [dict(x) for x in eig.get("benutzer", [])]
    dlg = Gtk.Window(transient_for=w, modal=True, title="%s Eigenschaft" % d.anzeigename())
    dlg.set_default_size(440, 580)
    haupt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    for r in ("start", "end", "top", "bottom"):
        getattr(haupt, "set_margin_" + r)(10)
    nb = Gtk.Notebook(vexpand=True)

    def seite_box():
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        for r in ("start", "end", "top", "bottom"):
            getattr(b, "set_margin_" + r)(10)
        return b

    # ---- Allgemein
    allg = seite_box()
    name = Gtk.Label(label=d.anzeigename(), selectable=True)
    name.set_margin_top(10)
    name.set_margin_bottom(10)
    allg.append(name)
    allg.append(Gtk.Separator())
    st = os.stat(d.pfad) if d.pfad and os.path.exists(d.pfad) else None

    def zt(t):
        return time.strftime("%d.%m.%Y %H:%M", time.localtime(t))
    ext = os.path.splitext(d.pfad)[1].lstrip(".").upper() if d.pfad else ""
    zeilen = [
        ("Typ", (ext + "-Datei") if ext else ""),
        ("Speicherort", os.path.dirname(d.pfad) if d.pfad else ""),
        ("Größe", ("%d Byte" % st.st_size) if st else ""), None,
        ("Dateiname von MS-DOS", (os.path.basename(d.pfad).upper()[:12]) if d.pfad else ""),
        ("Erstellt", zt(getattr(st, "st_ctime", 0)) if st else ""),
        ("Geändert", zt(st.st_mtime) if st else ""),
        ("Letzter Zugriff", zt(st.st_atime) if st else ""),
    ]
    for z in zeilen:
        if z is None:
            allg.append(Gtk.Separator())
            continue
        r = Gtk.Box(spacing=6)
        r.append(Gtk.Label(label=z[0] + ":", xalign=0))
        r.append(Gtk.Label(label=z[1], xalign=0, selectable=True, hexpand=True))
        allg.append(r)
    allg.append(Gtk.Separator())
    attr = Gtk.Box(spacing=10)
    attr.append(Gtk.Label(label="Attribute:"))
    for n, an in (("Schreibgeschützt", bool(st and not os.access(d.pfad, os.W_OK))), ("Ausgeblendet", bool(d.pfad and os.path.basename(d.pfad).startswith(".")))):
        c = Gtk.CheckButton(label=n, active=an, sensitive=False)
        attr.append(c)
    allg.append(attr)
    nb.append_page(allg, Gtk.Label(label="Allgemein"))

    # ---- Zusammenfassung
    zus = seite_box()
    felder = {}
    for n in _ZUS:
        r = Gtk.Box(spacing=6)
        r.append(Gtk.Label(label=n + ":", xalign=0, width_chars=11))
        e = Gtk.Entry(hexpand=True, text=eig.get(n, GLib.get_real_name() if n == "Autor" and n not in eig else ""))
        r.append(e)
        zus.append(r)
        felder[n] = e
    r = Gtk.Box(spacing=6, vexpand=True)
    r.append(Gtk.Label(label="Kommentare:", xalign=0, yalign=0.5, width_chars=11))
    kom = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD, hexpand=True)
    kom.get_buffer().set_text(eig.get("Kommentare", ""))
    sc = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    sc.set_child(kom)
    sc.set_has_frame(True)
    r.append(sc)
    zus.append(r)
    vor = Gtk.CheckButton(label="Vorschaugrafik speichern", active=bool(eig.get("Vorschaugrafik")))
    zus.append(vor)
    nb.append_page(zus, Gtk.Label(label="Zusammenfassung"))

    # ---- Benutzerdefiniert
    ben = seite_box()
    zeile = Gtk.Box(spacing=8)
    zeile.append(Gtk.Label(label="Name:", xalign=0, width_chars=6))
    pname = Gtk.Entry(hexpand=True)
    zeile.append(pname)
    ben.append(zeile)
    mitte = Gtk.Box(spacing=8)
    vorl = Gtk.ListBox()
    for v in _VORSCHLAEGE:
        vorl.append(Gtk.Label(label=v, xalign=0))
    vorl.connect("row-activated", lambda lb, row: pname.set_text(row.get_child().get_label()))
    sc2 = Gtk.ScrolledWindow(hexpand=True, min_content_height=120)
    sc2.set_child(vorl)
    sc2.set_has_frame(True)
    mitte.append(sc2)
    knp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, valign=Gtk.Align.START)
    plus = Gtk.Button(label="Hinzufügen")
    minus = Gtk.Button(label="Löschen")
    knp.append(plus)
    knp.append(minus)
    mitte.append(knp)
    ben.append(mitte)
    z2 = Gtk.Box(spacing=8)
    z2.append(Gtk.Label(label="Typ:", xalign=0, width_chars=6))
    typ = Gtk.DropDown.new_from_strings(["Text", "Datum", "Zahl", "Ja/Nein"])
    typ.set_hexpand(True)
    z2.append(typ)
    ben.append(z2)
    z3 = Gtk.Box(spacing=8)
    z3.append(Gtk.Label(label="Wert:", xalign=0, yalign=0, width_chars=6))
    wert = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD)
    sc3 = Gtk.ScrolledWindow(hexpand=True, min_content_height=60)
    sc3.set_child(wert)
    sc3.set_has_frame(True)
    z3.append(sc3)
    ben.append(z3)
    ben.append(Gtk.Label(label="Eigenschaft:", xalign=0))
    liste = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
    sc4 = Gtk.ScrolledWindow(vexpand=True, min_content_height=110)
    sc4.set_child(liste)
    sc4.set_has_frame(True)
    ben.append(sc4)

    def neu_zeichnen():
        while (c := liste.get_first_child()) is not None:
            liste.remove(c)
        for x in benutzer:
            zl = Gtk.Box(spacing=10, homogeneous=True)
            for t in (x["name"], x["wert"], x["typ"]):
                zl.append(Gtk.Label(label=t, xalign=0))
            liste.append(zl)

    def hinzu(*_):
        n = pname.get_text().strip()
        if not n:
            return
        b = wert.get_buffer()
        wt = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        benutzer[:] = [x for x in benutzer if x["name"] != n]
        benutzer.append({"name": n, "wert": wt, "typ": ["Text", "Datum", "Zahl", "Ja/Nein"][typ.get_selected()]})
        neu_zeichnen()
        pname.set_text("")
        b.set_text("")

    def weg(*_):
        row = liste.get_selected_row()
        if row is not None:
            del benutzer[row.get_index()]
            neu_zeichnen()
    plus.connect("clicked", hinzu)
    minus.connect("clicked", weg)
    neu_zeichnen()
    nb.append_page(ben, Gtk.Label(label="Benutzerdefiniert"))
    haupt.append(nb)

    knoepfe = Gtk.Box(spacing=8, halign=Gtk.Align.END)
    ab = Gtk.Button(label="Cancel")
    ab.connect("clicked", lambda *_: dlg.close())
    ok = Gtk.Button(label="OK")
    ok.add_css_class("suggested-action")

    def fertig(*_):
        for n, e in felder.items():
            eig[n] = e.get_text()
        b = kom.get_buffer()
        eig["Kommentare"] = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
        eig["Vorschaugrafik"] = vor.get_active()
        eig["benutzer"] = benutzer
        d.puffer.set_modified(True)
        dlg.close()
    ok.connect("clicked", fertig)
    knoepfe.append(ab)
    knoepfe.append(ok)
    haupt.append(knoepfe)
    dlg.set_child(haupt)
    dlg.set_default_widget(ok)
    dlg.present()


@befehl("umbenennen")
def _umbenennen(w, _=None):
    d = w.dok()
    if not d:
        return

    def ok(v):
        neu = v[0].strip()
        if not neu:
            return
        if d.pfad:
            ziel = os.path.join(os.path.dirname(d.pfad), neu if os.path.splitext(neu)[1] else neu + os.path.splitext(d.pfad)[1])
            try:
                os.rename(d.pfad, ziel)
            except OSError as e:
                return w.meldung("Umbenennen fehlgeschlagen", str(e))
            d.pfad = ziel
        else:
            d.titel = neu
        w._titel_auffrischen(d)
    hilfen.frage(w, "Umbenennen", [("Neuer Name", os.path.basename(d.pfad) if d.pfad else d.titel)], ok)


@befehl("schliessen")
def _schliessen(w, _=None):
    w.tab_schliessen()


@befehl("beenden")
def _beenden(w, _=None):
    w.close()


@befehl("rueckgaengig")
def _rueck(w, _=None):
    d = w.dok()
    if d:
        d.puffer.undo()


@befehl("wiederholen")
def _wieder(w, _=None):
    d = w.dok()
    if d:
        d.puffer.redo()


@befehl("ueber")
def _ueber(w, _=None):
    about = Gtk.AboutDialog(transient_for=w, modal=True)
    about.set_program_name("Lunivo-Office")
    about.set_version("GTK4")
    about.set_comments("Schreibprogramm mit der Schreibhilfe fest an der Seite. "
                       "Nicht für Menschen mit Legasthenie gebaut, sondern von einem.\n"
                       "Läuft ohne Konto und ohne Internet.")
    about.set_logo_icon_name("lunivo-office")
    about.set_license_type(Gtk.License.MIT_X11)
    about.present()


# ================================================================ Optionen, Hilfe
def _optionen(w, seite=None):
    from .optionen import oeffnen
    oeffnen(w, seite)


@befehl("optionen")
def _optionen_befehl(w, seite=None):
    _optionen(w, seite)


@befehl("handbuch")
def _handbuch(w, _=None):
    pfad = os.path.join(pfade.PROJEKT, "oberflaeche", "handbuch.html")
    if not os.path.exists(pfad):
        return w.meldung("Handbuch", "Die Handbuch-Datei fehlt: %s" % pfad)
    d = w.datei_oeffnen(pfad)
    if d:
        d.pfad = None
        d.titel = "Handbuch"
        d.puffer.set_modified(False)
        d.ansicht.set_editable(False)
        w._titel_auffrischen(d)


@befehl("tasten_hilfe")
def _tasten(w, _=None):
    from .. import menues
    namen = {"neu": "Neu", "oeffnen": "Öffnen", "speichern": "Speichern", "speichern_unter": "Speichern unter",
             "drucken": "Drucken", "schliessen": "Schließen", "beenden": "Beenden", "handbuch": "Handbuch",
             "optionen": "Optionen", "rueckgaengig": "Rückgängig", "wiederholen": "Wiederholen",
             "alles_markieren": "Alles auswählen", "suchen": "Suchen", "ersetzen": "Ersetzen", "fett": "Fett",
             "kursiv": "Kursiv", "unter": "Unterstrichen", "links": "Linksbündig", "mitte": "Zentriert",
             "rechts": "Rechtsbündig", "block": "Blocksatz", "seitenumbruch": "Seitenumbruch", "pruefen": "Schreibhilfe prüfen",
             "tafel_zeigen": "Schreibhilfe ein/aus", "textbaustein": "Textbaustein", "groesser": "Vergrößern",
             "kleiner": "Verkleinern", "hyperlink": "Hyperlink"}
    zeilen = []
    for k, tasten in sorted(menues.TASTEN.items(), key=lambda x: namen.get(x[0].split("|")[0], x[0])):
        n = namen.get(k.split("|")[0], k.split("|")[0])
        t = tasten[0].replace("<Primary>", "Strg+").replace("<Shift>", "Umschalt+").replace("<Alt>", "Alt+")
        zeilen.append("%-26s %s" % (n, t))
    zeilen += ["", "%-26s %s" % ("Hyperlink öffnen", "Strg + Klick"), "%-26s %s" % ("Wortvorhersage übernehmen", "Tab"),
               "%-26s %s" % ("Lesemodus beenden", "Esc")]
    dlg = Gtk.Window(transient_for=w, title="Tastenkürzel")
    dlg.set_default_size(420, 520)
    tv = Gtk.TextView(editable=False, monospace=True)
    tv.get_buffer().set_text("\n".join(zeilen))
    tv.set_left_margin(12)
    tv.set_top_margin(10)
    r = Gtk.ScrolledWindow()
    r.set_child(tv)
    dlg.set_child(r)
    dlg.present()


@befehl("erweiterungen")
def _erweiterungen(w, _=None):
    import shutil
    zeilen = []
    for name, ok, wofuer in (("LibreOffice (soffice)", shutil.which("soffice"), "Word-, OpenDocument- und PDF-Dateien"),
                              ("Node.js", shutil.which("node"), "Schreibhilfe (Regelprüfung)"),
                              ("Enchant/Hunspell", shutil.which("enchant-2"), "Rechtschreibung"),
                              ("Speech Dispatcher (spd-say)", shutil.which("spd-say"), "Vorlesen"),
                              ("Ollama", shutil.which("ollama"), "KI auf diesem Rechner"),
                              ("gnome-screenshot", shutil.which("gnome-screenshot"), "Bildschirmfoto"),
                              ("wmctrl", shutil.which("wmctrl"), "Fenster anordnen")):
        zeilen.append("%s  %s — %s" % ("✓" if ok else "✗", name, wofuer))
    zeilen.append("\nSchriften zum leichteren Lesen (OpenDyslexic, Lexend, Atkinson): ./schrift-holen.sh --alle")
    w.meldung("Erweiterungen und Hilfsprogramme", "\n".join(zeilen))


@befehl("speichern_bild")
def _speichern_bild(w, _=None):
    """Als Bild exportieren: Jede Seite / Lange Grafik, Wasserzeichen, Qualität, Format, Zielordner."""
    import shutil
    import subprocess
    import tempfile
    import threading
    d = w.dok()
    if not d:
        return
    dlg = Gtk.Window(transient_for=w, modal=True, title="Als Bild exportieren")
    dlg.set_default_size(640, -1)
    dlg.set_resizable(False)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    for r in ("start", "end", "top", "bottom"):
        getattr(box, "set_margin_" + r)(20)
    kachel = Gtk.Box(spacing=18, homogeneous=True)
    art = {"modus": "seiten"}
    erster = None
    for schl, text, icon in (("seiten", "Jede Seite", "view-grid-symbolic"), ("lang", "Lange Grafik", "view-paged-symbolic")):
        k = Gtk.ToggleButton()
        inhalt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bild = Gtk.Image.new_from_icon_name(icon)
        bild.set_pixel_size(72)
        inhalt.append(bild)
        inhalt.append(Gtk.Label(label=text))
        k.set_child(inhalt)
        k.set_size_request(-1, 130)
        if erster:
            k.set_group(erster)
        else:
            erster = k
        k.set_active(schl == "seiten")
        k.connect("toggled", lambda b, s=schl: b.get_active() and art.update(modus=s))
        kachel.append(k)
    box.append(kachel)

    def zeile(name, widget):
        z = Gtk.Box(spacing=10)
        z.append(Gtk.Label(label=name, xalign=0, width_chars=14))
        widget.set_hexpand(True)
        z.append(widget)
        box.append(z)
    wasser = Gtk.Entry(placeholder_text="Vertraulich, Kopieren verboten, Originalkopie, Muster …")
    zeile("Wasserzeichen", wasser)
    qual = Gtk.DropDown.new_from_strings(["Standard", "Hoch", "Sehr hoch"])
    zeile("Qualität", qual)
    fmt = Gtk.DropDown.new_from_strings(["PNG", "JPG"])
    zeile("Format", fmt)
    ziel = Gtk.Entry(text=w.werte.get("bild_ordner") or os.path.join(os.path.expanduser("~"), "Bilder"))
    ziel_zeile = Gtk.Box(spacing=6)
    ziel.set_hexpand(True)
    ziel_zeile.append(ziel)
    waehlen = Gtk.Button(label="…")

    def ordner_waehlen(*_):
        fd = Gtk.FileDialog(title="Speichern unter")

        def fertig(fd, res):
            try:
                o = fd.select_folder_finish(res)
            except GLib.Error:
                return
            ziel.set_text(o.get_path())
        fd.select_folder(dlg, None, fertig)
    waehlen.connect("clicked", ordner_waehlen)
    ziel_zeile.append(waehlen)
    zeile("Speichern unter", ziel_zeile)
    unten = Gtk.Box(spacing=8, halign=Gtk.Align.END)
    abbrechen = Gtk.Button(label="Abbrechen")
    abbrechen.connect("clicked", lambda *_: dlg.close())
    los = Gtk.Button(label="Exportieren")
    los.add_css_class("suggested-action")

    def exportieren(*_):
        ordner = ziel.get_text().strip()
        endung = ["png", "jpg"][fmt.get_selected()]
        dpi = [100, 200, 300][qual.get_selected()]
        marke = wasser.get_text().strip()
        modus = art["modus"]
        basis = os.path.splitext(d.anzeigename())[0] or "Dokument"
        w.werte["bild_ordner"] = ordner
        dlg.close()
        w.status("Exportiere Bild …")

        def arbeit():
            tmp = tempfile.mkdtemp(prefix="lunivo-bild-")
            try:
                os.makedirs(ordner, exist_ok=True)
                pdf = os.path.join(tmp, "seiten.pdf")
                d.speichern_unter(pdf)
                fmtopt = "-png" if endung == "png" else "-jpeg"
                subprocess.run(["pdftoppm", fmtopt, "-r", str(dpi), pdf, os.path.join(tmp, "s")],
                               check=True, capture_output=True, timeout=300)
                seiten = sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("s-"))
                if marke:
                    for sp in seiten:
                        subprocess.run(["convert", sp, "-gravity", "center", "-fill", "rgba(120,120,120,0.35)",
                                        "-pointsize", str(max(24, dpi // 2)), "-annotate", "315x315+0+0", marke, sp],
                                       check=True, capture_output=True, timeout=120)
                ergebnis = []
                if modus == "lang" and len(seiten) > 1:
                    ausgabe = os.path.join(ordner, "%s.%s" % (basis, endung))
                    subprocess.run(["convert"] + seiten + ["-append", ausgabe], check=True, capture_output=True, timeout=300)
                    ergebnis.append(ausgabe)
                else:
                    for i, sp in enumerate(seiten, 1):
                        ausgabe = os.path.join(ordner, ("%s-%d.%s" % (basis, i, endung)) if len(seiten) > 1 else ("%s.%s" % (basis, endung)))
                        shutil.copyfile(sp, ausgabe)
                        ergebnis.append(ausgabe)
                GLib.idle_add(w.status, "Exportiert: %d Bild(er) in %s" % (len(ergebnis), ordner))
            except Exception as e:
                GLib.idle_add(w.meldung, "Export fehlgeschlagen", str(e))
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        threading.Thread(target=arbeit, daemon=True).start()
    los.connect("clicked", exportieren)
    unten.append(abbrechen)
    unten.append(los)
    box.append(unten)
    dlg.set_child(box)
    dlg.set_default_widget(los)
    dlg.present()
