from PySide6.QtCore import QSettings, QStandardPaths

from native_qt.storage import recovery
from native_qt.storage.settings import Settings


def test_settings_persist_and_recent(app, tmp_path):
    ini = str(tmp_path / "s.ini")
    s = Settings(QSettings(ini, QSettings.IniFormat))
    s.set("theme", "dark"); s.set("n", 7)
    for i in range(20):
        s.add_recent(f"/x/{i}.docx")
    s.add_recent("/x/5.docx")
    s2 = Settings(QSettings(ini, QSettings.IniFormat))
    assert s2.get("theme") == "dark" and s2.get_int("n", 0) == 7
    r = s2.recent()
    assert r[0] == "/x/5.docx" and len(r) == 12 and len(set(r)) == 12
    s2.remove_recent("/x/5.docx")
    assert "/x/5.docx" not in s2.recent()


def test_recovery_cycle(app, tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, "recovery_dir", lambda: str(tmp_path))
    t = recovery.new_token()
    d, m = recovery.paths(t)
    open(d, "wb").write(b"x")
    recovery.write_meta(t, "/a/b.docx", "b")
    e = recovery.pending()
    assert len(e) == 1 and e[0].original == "/a/b.docx"
    assert recovery.pending(exclude={t}) == []
    recovery.discard(t)
    assert recovery.pending() == []
