"""Rechtschreibung (Enchant/Hunspell), Silbentrennung (Wörterbuch hyph_*.dic), Thesaurus (MyThes)."""
import os
import re
import shutil
import subprocess

WORT = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*", re.UNICODE)

SPRACHEN = {"de_DE": "Deutsch (Deutschland)", "de_AT": "Deutsch (Österreich)", "de_CH": "Deutsch (Schweiz)",
            "en_US": "Englisch (USA)"}


# ------------------------------------------------------------------ Rechtschreibung
def sprachen_da():
    d = "/usr/share/hunspell"
    try:
        namen = {f[:-4] for f in os.listdir(d) if f.endswith(".dic")}
    except OSError:
        return []
    return [(k, v) for k, v in SPRACHEN.items() if k in namen]


def pruefen(text, sprache="de_DE", eigene=()):
    """[(von, bis, wort, [vorschläge])] — Positionen in Zeichen."""
    prog = shutil.which("enchant-2")
    if not prog:
        return []
    treffer = [(m.start(), m.end(), m.group(0)) for m in WORT.finditer(text)]
    einmalig = sorted({w for _, _, w in treffer if len(w) > 1 and w not in eigene})
    if not einmalig:
        return []
    eingabe = "\n".join("^" + w for w in einmalig) + "\n"
    try:
        lauf = subprocess.run([prog, "-d", sprache, "-a"], input=eingabe.encode("utf-8"),
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    falsch = {}
    for zeile in lauf.stdout.decode("utf-8", "replace").splitlines():
        if zeile.startswith("&"):
            kopf, _, vor = zeile.partition(":")
            wort = kopf.split()[1]
            falsch[wort] = [v.strip() for v in vor.split(",")][:6]
        elif zeile.startswith("#"):
            falsch[zeile.split()[1]] = []
    return [(a, b, w, falsch[w]) for a, b, w in treffer if w in falsch]


def vorschlaege(wort, sprache="de_DE"):
    prog = shutil.which("enchant-2")
    if not prog:
        return []
    lauf = subprocess.run([prog, "-d", sprache, "-a"], input=("^" + wort + "\n").encode("utf-8"),
                          capture_output=True, timeout=10)
    for zeile in lauf.stdout.decode("utf-8", "replace").splitlines():
        if zeile.startswith("&"):
            return [v.strip() for v in zeile.partition(":")[2].split(",")][:8]
    return []


# ------------------------------------------------------------------ Silbentrennung
_muster_cache = {}


def _muster(sprache="de_DE"):
    if sprache in _muster_cache:
        return _muster_cache[sprache]
    pfad = "/usr/share/hyphen/hyph_%s.dic" % sprache
    if not os.path.exists(pfad):
        pfad = "/usr/share/hyphen/hyph_de.dic"
    muster, min_l, min_r = {}, 2, 2
    try:
        with open(pfad, "rb") as f:
            roh = f.read()
        kodierung = roh.split(b"\n", 1)[0].decode("ascii", "replace").strip() or "UTF-8"
        text = roh.decode(kodierung if kodierung.upper() != "UTF-8" else "utf-8", "replace")
        for zeile in text.splitlines()[1:]:
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#"):
                continue
            if zeile.startswith("LEFTHYPHENMIN"):
                min_l = int(zeile.split()[1])
                continue
            if zeile.startswith("RIGHTHYPHENMIN"):
                min_r = int(zeile.split()[1])
                continue
            if zeile == "NEXTLEVEL":
                break                                   # nur die erste Ebene
            if zeile.startswith(("COMPOUND", "NOHYPHEN", "ISO8859", "UTF-8")):
                continue
            zeile = zeile.split("/")[0]
            buchst, zahlen, vorher_zahl = "", [], False
            for ch in zeile:
                if ch.isdigit():
                    zahlen.append(int(ch))
                    vorher_zahl = True
                else:
                    if not vorher_zahl:
                        zahlen.append(0)
                    buchst += ch
                    vorher_zahl = False
            if not vorher_zahl:
                zahlen.append(0)
            muster[buchst] = zahlen
    except OSError:
        pass
    _muster_cache[sprache] = (muster, min_l, min_r)
    return _muster_cache[sprache]


def trennstellen(wort, sprache="de_DE"):
    """Positionen (Index vor dem Zeichen), an denen getrennt werden darf."""
    muster, min_l, min_r = _muster(sprache)
    w = "." + wort.lower() + "."
    werte = [0] * (len(w) + 1)
    for i in range(len(w)):
        for j in range(i + 1, min(len(w), i + 12) + 1):
            z = muster.get(w[i:j])
            if z:
                for k, v in enumerate(z):
                    if v > werte[i + k]:
                        werte[i + k] = v
    stellen = []
    for pos in range(1, len(wort)):
        if werte[pos + 1] % 2 == 1 and pos >= min_l + 0 and len(wort) - pos >= min_r + 0:
            stellen.append(pos)
    return stellen


def mit_trennung(text, sprache="de_DE", minlaenge=7):
    """Fügt in langen Wörtern weiche Trennstriche (U+00AD) ein."""
    def ersetze(m):
        w = m.group(0)
        if len(w) < minlaenge:
            return w
        teile, letzte = [], 0
        for p in trennstellen(w, sprache):
            teile.append(w[letzte:p])
            letzte = p
        teile.append(w[letzte:])
        return "­".join(teile)
    return WORT.sub(ersetze, text)


# ------------------------------------------------------------------ Thesaurus
_thes = {}


def _thes_laden(sprache):
    if sprache in _thes:
        return _thes[sprache]
    idx = "/usr/share/mythes/th_%s_v2.idx" % sprache
    dat = "/usr/share/mythes/th_%s_v2.dat" % sprache
    if not os.path.exists(idx):
        idx, dat = idx.replace("_v2", "").replace(sprache, "de_DE"), dat.replace(sprache, "de_DE")
    tabelle = {}
    try:
        with open(idx, encoding="utf-8", errors="replace") as f:
            zeilen = f.read().splitlines()[2:]
        for z in zeilen:
            w, _, o = z.rpartition("|")
            if w and o.isdigit():
                tabelle[w.lower()] = int(o)
        _thes[sprache] = (tabelle, dat)
    except OSError:
        _thes[sprache] = ({}, dat)
    return _thes[sprache]


def synonyme(wort, sprache="de_DE"):
    """[(Wortart, [Synonyme])] oder []."""
    tabelle, dat = _thes_laden(sprache)
    ort = tabelle.get(wort.lower())
    if ort is None:
        return []
    with open(dat, "rb") as f:
        f.seek(ort)
        kopf = f.readline().decode("utf-8", "replace").strip()
        n = int(kopf.rpartition("|")[2] or 0)
        ergebnis = []
        for _ in range(n):
            teile = f.readline().decode("utf-8", "replace").strip().split("|")
            ergebnis.append((teile[0].strip("()"), [t for t in teile[1:] if t]))
    return ergebnis
