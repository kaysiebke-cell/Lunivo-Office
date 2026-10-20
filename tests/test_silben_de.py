"""Deutsche Sprechsilben: Soll-Liste (tests/silben_gold.py, 228 Wörter, von Hand geprüft) und eine harte Liste mit bekannten Fehlern."""
import os

from lunivo_writer.proofing.silben_de import silben
from silben_gold import GOLD


def _paare(text):
    return [z.split() for z in text.splitlines() if z.strip()]


def test_gold_alle_richtig():
    falsch = [(w, s, "-".join(silben(w))) for w, s in _paare(GOLD) if "-".join(silben(w)).lower() != s.lower()]
    assert not falsch, falsch


def test_harte_liste_quote_und_bekannte_fehler():
    """Seltenere Wörter, Fremdwörter, Zusammensetzungen: mindestens 90 % richtig; die bekannten Fehler stehen hier offen."""
    pfad = os.path.join(os.path.dirname(__file__), "silben_hart.txt")
    paare = _paare(open(pfad, encoding="utf-8").read())
    falsch = {w: "-".join(silben(w)) for w, s in paare if "-".join(silben(w)).lower() != s.lower()}
    assert len(falsch) / len(paare) <= 0.10, falsch
    # bekannte Grenzen (richtig wäre in Klammern): Zusammensetzungen mit vokalischem zweiten Teil, einzelne Fremdwörter
    assert set(falsch) <= {"Chirurg", "Restaurant", "Zusammenarbeit"}, falsch


def test_sonderfaelle():
    assert silben("Fo") == ("Fo",) and silben("a") == ("a",)
    assert silben("ABC123") == ("ABC123",) and silben("e-mail") == ("e-mail",)
    assert silben("Äpfel") == ("Äp", "fel") and "".join(silben("Überraschung")) == "Überraschung"       # nichts geht verloren
    assert "".join(silben("Straße")) == "Straße"
