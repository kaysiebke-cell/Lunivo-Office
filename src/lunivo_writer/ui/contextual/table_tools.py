"""Kontext-Reiter „Tabellentools“ (erscheint, wenn die Schreibmarke in einer Tabelle steht)."""
from __future__ import annotations

from lunivo_writer.ui.ribbon.tabs.baustein import k as _k


TABELLENTOOLS = {"name": "Tabellentools", "kontext": "tabelle", "gruppen": [
    {"name": "Entwurf: Rahmen und Farbe", "knoepfe": [
        _k("rahmen", "Rahmenlinien ein/aus", "tabelleRahmen", True, haken=True),
        _k("toenung", "Zellenschattierung", klappe="tabelleSchattierung", gross=True)]},
    {"name": "Layout: Zeilen und Spalten", "knoepfe": [
        _k("kanteOben", "Zeile oberhalb einfügen", "tabelleZeileOben"),
        _k("kanteUnten", "Zeile unterhalb einfügen", "tabelleZeileUnten"),
        _k("kanteLinks", "Spalte links einfügen", "tabelleSpalteLinks"),
        _k("kanteRechts", "Spalte rechts einfügen", "tabelleSpalteRechts"),
        _k("//", "x"),
        _k("kanteKeine", "Zeile löschen", "tabelleZeileLoeschen"),
        _k("kanteKeine", "Spalte löschen", "tabelleSpalteLoeschen"),
        _k("kanteKeine", "Tabelle löschen", "tabelleLoeschen")]},
    {"name": "Zellen", "knoepfe": [
        _k("kanteAlle", "Zellen verbinden", "tabelleVerbinden"),
        _k("kanteInnen", "Zelle teilen", "tabelleTeilen"),
        _k("sortieren", "Tabelle sortieren", "tabelleSortieren")]},
    {"name": "Ausrichtung", "knoepfe": [
        _k("links", "Oben ausrichten", "zelleOben"),
        _k("mitte", "Mittig ausrichten", "zelleMitte"),
        _k("rechts", "Unten ausrichten", "zelleUnten")]},
]}
