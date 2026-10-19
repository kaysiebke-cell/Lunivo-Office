"""Dokumentkennwort: AES-256-GCM, Schlüssel aus dem Kennwort per PBKDF2 (200 000 Runden)."""
import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KENNUNG = "lunivo-verschluesselt"


class KennwortNoetig(Exception):
    pass


class KennwortFalsch(Exception):
    pass


def _schluessel(kennwort, salz):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salz, iterations=200_000).derive(kennwort.encode("utf-8"))


def verschluesseln(text, kennwort):
    salz, nonce = os.urandom(16), os.urandom(12)
    daten = AESGCM(_schluessel(kennwort, salz)).encrypt(nonce, text.encode("utf-8"), None)
    return json.dumps({KENNUNG: 1, "salz": base64.b64encode(salz).decode(), "nonce": base64.b64encode(nonce).decode(),
                       "daten": base64.b64encode(daten).decode()})


def ist_verschluesselt(text):
    return text.lstrip().startswith("{") and ('"%s"' % KENNUNG) in text[:80]


def entschluesseln(text, kennwort):
    j = json.loads(text)
    try:
        roh = AESGCM(_schluessel(kennwort, base64.b64decode(j["salz"]))).decrypt(
            base64.b64decode(j["nonce"]), base64.b64decode(j["daten"]), None)
    except Exception:
        raise KennwortFalsch()
    return roh.decode("utf-8")
