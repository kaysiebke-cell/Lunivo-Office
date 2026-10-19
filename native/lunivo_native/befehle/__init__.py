"""Die Befehle hinter den Knöpfen.

Ein Befehl ist eine Funktion f(fenster, arg=None), registriert mit @befehl("name").
Eine Klappe (Auswahl unter einem Knopf) ist f(fenster, popover) -> Widget,
registriert mit @klappe("name"). Was hier fehlt, erscheint im Band nicht."""
import importlib

_BEFEHLE = {}
_KLAPPEN = {}
_SONDER = {}


def befehl(name):
    def deko(f):
        _BEFEHLE[name] = f
        return f
    return deko


def klappe(name):
    def deko(f):
        _KLAPPEN[name] = f
        return f
    return deko


def sonder(name):
    def deko(f):
        _SONDER[name] = f
        return f
    return deko


def gibt_es(name):
    return name in _BEFEHLE


def gibt_klappe(name):
    return name in _KLAPPEN


def ausfuehren(fenster, name, arg=None):
    f = _BEFEHLE.get(name)
    if f is None:
        fenster.status("Befehl „%s“ gibt es noch nicht." % name)
        return False
    try:
        return f(fenster, arg)
    except Exception as e:                           # ein Befehl darf das Programm nie beenden
        import traceback
        traceback.print_exc()
        fenster.meldung("Das hat nicht geklappt", "%s: %s" % (type(e).__name__, e))
        return False


befehle_ausfuehren = ausfuehren


def klappe_bauen(fenster, name, popover):
    f = _KLAPPEN.get(name)
    return f(fenster, popover) if f else None


def felder_bauen(fenster):
    return _SONDER["felder"](fenster)


def katalog_bauen(fenster):
    f = _SONDER.get("katalog")
    return f(fenster) if f else None


def raender_bauen(fenster):
    f = _SONDER.get("raender")
    return f(fenster) if f else None


def alle_laden():
    for m in ("hilfen", "start", "einfuegen", "seitenlayout", "referenzen",
              "ueberpruefen", "schreibhilfe_tab", "sendungen", "ansicht", "datei", "werkzeuge"):
        try:
            importlib.import_module("%s.%s" % (__name__, m))
        except ModuleNotFoundError as e:
            if e.name != "%s.%s" % (__name__, m):
                raise
