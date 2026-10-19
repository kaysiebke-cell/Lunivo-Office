#!/usr/bin/env python3
"""Einstieg: python -m lunivo_writer [Datei …]"""
from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    try:
        import PySide6.QtWidgets  # noqa: F401
    except ImportError:
        print("PySide6 fehlt. Installieren mit:  ./starten-qt.sh   (legt eine eigene Umgebung an)\n"
              "oder:  pip install -r requirements.txt", file=sys.stderr)
        return 2
    from lunivo_writer.core.application import LunivoApplication
    return LunivoApplication(argv).start()


if __name__ == "__main__":
    sys.exit(main())
