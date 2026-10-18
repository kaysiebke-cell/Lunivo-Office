#!/usr/bin/env python3
"""Wandelt oberflaeche/handbuch.html (Web-Fassung) in native_qt/resources/handbuch.md um (Qt kann HTML → Markdown).
Die native Fassung enthält so keine HTML-Dateien; das Handbuch wird als Markdown im Hilfefenster angezeigt."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QTextDocument  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = QApplication(sys.argv[:1])
d = QTextDocument()
d.setHtml(open(os.path.join(WURZEL, "oberflaeche/handbuch.html"), encoding="utf-8").read())
md = d.toMarkdown()
ziel = os.path.join(WURZEL, "native_qt/resources/handbuch.md")
open(ziel, "w", encoding="utf-8").write(md)
print(len(md), "Zeichen →", ziel)
