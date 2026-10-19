#!/bin/sh
#
# haken-an.sh — die Prüfungen vor dem Commit einschalten.
#
# Git sucht seine Haken normalerweise in .git/hooks. Dieser Ordner wird
# nicht mitversioniert: Was dort liegt, hat nur der eine Rechner, auf dem
# es angelegt wurde. Deshalb liegen die Haken hier im Projekt, und Git
# wird einmal gesagt, dass es sie dort suchen soll.
#
#     ./werkzeug/haken-an.sh        einschalten
#     ./werkzeug/haken-an.sh --weg  wieder abschalten

wurzel=$(git rev-parse --show-toplevel) || { echo "Kein Git-Projekt."; exit 1; }
cd "$wurzel" || exit 1

if [ "$1" = "--weg" ]; then
  git config --unset core.hooksPath 2>/dev/null
  echo "Abgeschaltet. Git sucht seine Haken wieder in .git/hooks."
  exit 0
fi

git config core.hooksPath werkzeug/git-haken
echo "Eingeschaltet: Vor jedem Commit werden die Namen geprüft."
echo "Abschalten mit: ./werkzeug/haken-an.sh --weg"
