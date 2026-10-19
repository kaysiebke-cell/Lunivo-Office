"""Reiter „Verweise“ (in register.json „Referenzen“)."""
from __future__ import annotations


def bauen(register: dict) -> dict:
    return dict(next(t for t in register["register"] if t["name"] == "Referenzen"), name="Verweise")
