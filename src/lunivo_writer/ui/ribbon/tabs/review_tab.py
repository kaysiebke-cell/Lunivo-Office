"""Reiter „Überprüfen“: Gruppen aus register.json."""
from __future__ import annotations


def bauen(register: dict) -> dict:
    return next(t for t in register["register"] if t["name"] == "Überprüfen")
