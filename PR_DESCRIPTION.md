## PR: README → docs/ (Umstrukturierung)

Diese PR teilt die bisher sehr ausführliche README in thematische Seiten unter `docs/` auf und ersetzt die Root-`README.md` durch eine kompakte Landing‑Seite, die auf die neuen Dokumente verweist.

Änderungen:
- Neuer Branch: `docs/restructure-readme-1`
- Neue Dateien unter `docs/`: quick-start.md, requirements.md, feature-overview.md, oberflaeche.md, pruefung-und-schreibhilfe.md, tts-und-stimmen.md, project-structure.md, dev-tools.md, keyboard-shortcuts.md, examples.md, known-limitations.md
- `README.md` wurde gekürzt und verweist auf `docs/`.
- `doku/LIESMICH.md` bleibt als vollständiges Backup erhalten.

Bitte prüfe vor dem Merge besonders:
- interne Links und Bildpfade (bilder/) funktionieren noch korrekt
- gewünschte Sprache/Formatierung

Closes: keine
