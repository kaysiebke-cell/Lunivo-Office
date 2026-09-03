# -*- coding: utf-8 -*-
"""Rechnet ein Lucide-SVG in einen einzigen Pfad um.

Lucide zeichnet mit <path>, <circle>, <rect>, <line>, <polyline> und
<ellipse>. Unser symbol() setzt genau ein <path d="…">. Statt das Programm
umzubauen, werden die Grundformen in Pfadbefehle übersetzt — ein Kreis ist
zwei Halbbögen, ein Rechteck vier Linien, eine Linie ein M und ein L.
"""
import re, os, sys

def z(w):
    """Zahl kurz schreiben: 12.0 -> 12, 12.50 -> 12.5"""
    t = ('%.3f' % float(w)).rstrip('0').rstrip('.')
    return t if t not in ('-0', '') else '0'

def attr(tag, name, vor=0):
    m = re.search(r'\b%s="([^"]*)"' % name, tag)
    return float(m.group(1)) if m else float(vor)

def kreis(cx, cy, r):
    return 'M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 -%s 0' % (
        z(cx - r), z(cy), z(r), z(r), z(2 * r), z(r), z(r), z(2 * r))

def ellipse(cx, cy, rx, ry):
    return 'M%s %sa%s %s 0 1 0 %s 0a%s %s 0 1 0 -%s 0' % (
        z(cx - rx), z(cy), z(rx), z(ry), z(2 * rx), z(rx), z(ry), z(2 * rx))

def rechteck(x, y, w, h, rx, ry):
    if rx <= 0 and ry <= 0:
        return 'M%s %sh%sv%sh-%sz' % (z(x), z(y), z(w), z(h), z(w))
    rx = min(rx or ry, w / 2.0)
    ry = min(ry or rx, h / 2.0)
    return ('M%s %sh%sa%s %s 0 0 1 %s %sv%sa%s %s 0 0 1 -%s %sh-%s'
            'a%s %s 0 0 1 -%s -%sv-%sa%s %s 0 0 1 %s -%sz') % (
        z(x + rx), z(y), z(w - 2 * rx), z(rx), z(ry), z(rx), z(ry),
        z(h - 2 * ry), z(rx), z(ry), z(rx), z(ry), z(w - 2 * rx),
        z(rx), z(ry), z(rx), z(ry), z(h - 2 * ry), z(rx), z(ry), z(rx), z(ry))

def punkte(roh, zu=False):
    zahlen = [t for t in re.split(r'[\s,]+', roh.strip()) if t]
    paare = list(zip(zahlen[0::2], zahlen[1::2]))
    if not paare:
        return ''
    d = 'M' + z(paare[0][0]) + ' ' + z(paare[0][1])
    for x, y in paare[1:]:
        d += 'L' + z(x) + ' ' + z(y)
    return d + ('z' if zu else '')

def umbauen(svg):
    teile = []
    for treffer in re.finditer(r'<(path|circle|rect|line|polyline|polygon|ellipse)\b[^>]*>',
                               svg, re.S):
        tag = treffer.group(0)
        art = treffer.group(1)
        if art == 'path':
            m = re.search(r'\bd="([^"]*)"', tag)
            if m: teile.append(m.group(1).strip())
        elif art == 'circle':
            teile.append(kreis(attr(tag, 'cx'), attr(tag, 'cy'), attr(tag, 'r')))
        elif art == 'ellipse':
            teile.append(ellipse(attr(tag, 'cx'), attr(tag, 'cy'),
                                 attr(tag, 'rx'), attr(tag, 'ry')))
        elif art == 'rect':
            teile.append(rechteck(attr(tag, 'x'), attr(tag, 'y'),
                                  attr(tag, 'width'), attr(tag, 'height'),
                                  attr(tag, 'rx'), attr(tag, 'ry')))
        elif art == 'line':
            teile.append('M%s %sL%s %s' % (z(attr(tag, 'x1')), z(attr(tag, 'y1')),
                                           z(attr(tag, 'x2')), z(attr(tag, 'y2'))))
        elif art in ('polyline', 'polygon'):
            m = re.search(r'\bpoints="([^"]*)"', tag)
            if m: teile.append(punkte(m.group(1), art == 'polygon'))
    # Ein Pfad, der mit kleinem "m" beginnt, meint laut SVG-Norm trotzdem
    # absolute Koordinaten — ABER nur, solange er allein steht. Hängt man
    # ihn hinter einen anderen, wird daraus plötzlich "relativ zum Ende des
    # vorigen", und die Zeichnung fällt auseinander. Also groß schreiben.
    sauber = []
    for t in teile:
        t = t.strip()
        if not t:
            continue
        if t[0] == 'm':
            # Und es reicht nicht, das m groß zu schreiben: Nach einem
            # kleinen m sind die folgenden Zahlenpaare RELATIVE Linien,
            # nach einem großen M absolute. Also den Sprung absolut machen
            # und für den Rest ausdrücklich ein kleines l setzen.
            treffer = re.match(r'm\s*(-?[\d.]+)[\s,]+(-?[\d.]+)(.*)$', t, re.S)
            if treffer:
                rest = treffer.group(3).lstrip()
                if rest and (rest[0].isdigit() or rest[0] in '-.'):
                    rest = 'l' + rest
                t = 'M%s %s%s' % (treffer.group(1), treffer.group(2),
                                  (' ' + rest) if rest else '')
            else:
                t = 'M' + t[1:]
        sauber.append(t)
    return ' '.join(sauber)
