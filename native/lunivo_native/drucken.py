"""Drucken mit dem GTK-Druckdialog (Pango, ohne Umweg)."""
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Pango, PangoCairo  # noqa: E402

from . import html_io


def drucken(fenster, dokument, aktion=Gtk.PrintOperationAction.PRINT_DIALOG, datei=None):
    markup = html_io.puffer_in_pango(dokument.puffer)
    op = Gtk.PrintOperation()
    op.set_job_name(dokument.anzeigename())
    op.set_use_full_page(False)
    op.set_unit(Gtk.Unit.POINTS)
    zustand = {"seiten": [], "layout": None}

    def vorbereiten(op, ctx):
        layout = ctx.create_pango_layout()
        layout.set_width(int(ctx.get_width() * Pango.SCALE))
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_font_description(Pango.FontDescription("%s %d" % (dokument.vorgabe_schrift, dokument.vorgabe_groesse)))
        layout.set_markup(markup, -1)
        hoehe = ctx.get_height() * Pango.SCALE
        seiten, start, y, anzahl = [], 0, 0, layout.get_line_count()
        for i in range(anzahl):
            _, logisch = layout.get_line_readonly(i).get_extents()
            if y + logisch.height > hoehe and i > start:
                seiten.append((start, i))
                start, y = i, 0
            y += logisch.height
        seiten.append((start, anzahl))
        zustand["seiten"], zustand["layout"] = seiten, layout
        op.set_n_pages(len(seiten))

    def zeichnen(op, ctx, nr):
        cr = ctx.get_cairo_context()
        layout = zustand["layout"]
        von, bis = zustand["seiten"][nr]
        y0 = 0
        it = layout.get_iter()
        i = 0
        cr.set_source_rgb(0, 0, 0)
        while True:
            if von <= i < bis:
                zeile = it.get_line_readonly()
                _, logisch = it.get_line_extents()
                if i == von:
                    y0 = logisch.y
                cr.move_to(logisch.x / Pango.SCALE, (it.get_baseline() - y0) / Pango.SCALE)
                PangoCairo.show_layout_line(cr, zeile)
            i += 1
            if i >= bis or not it.next_line():
                break

    op.connect("begin-print", vorbereiten)
    op.connect("draw-page", zeichnen)
    if datei:
        op.set_export_filename(datei)
    return op.run(aktion, fenster)
