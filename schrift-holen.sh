#!/bin/bash
# ============================================================
# Schriften holen, die das Lesen leichter machen.
#
# Wer Legasthenie hat, liest nicht in jeder Schrift gleich gut. Drei sind
# eigens dafür gemacht worden, und alle drei sind frei:
#
#   OpenDyslexic  Die Buchstaben sind unten schwerer als oben. Das gibt
#                 ihnen ein Gewicht, und ein Gewicht hat eine Richtung —
#                 b und d, p und q lassen sich dann nicht mehr so leicht
#                 verwechseln. Ungewohnt am Anfang, für viele danach die
#                 mit dem größten Unterschied.
#
#   Lexend        Nicht gegen das Verwechseln gemacht, sondern für das
#                 Tempo: weite Buchstaben, viel Luft dazwischen. In Studien
#                 mit Kindern hat sie die Lesegeschwindigkeit erhöht.
#
#   Atkinson      Vom Braille Institute für Menschen mit wenig Sehkraft
#   Hyperlegible  entworfen. Sie unterscheidet die Formen, die einander
#                 ähneln, so weit wie möglich: I, l und 1; O und 0.
#
# Alles landet unter ~/.local/share/fonts/lunivo-office — nichts im System,
# nichts im Projekt. Zum Entfernen: ./schrift-holen.sh --weg
#
#   ./schrift-holen.sh                 OpenDyslexic, der Grundstock
#   ./schrift-holen.sh lexend atkinson weitere dazu
#   ./schrift-holen.sh --alle          alle drei
#   ./schrift-holen.sh --liste         nur zeigen, was es gibt
#   ./schrift-holen.sh --weg           alles wieder entfernen
#
# Alle drei stehen unter der SIL Open Font License 1.1: benutzen,
# weitergeben und verändern ist erlaubt, auch gewerblich.
# ============================================================
set -e

ZIEL="$HOME/.local/share/fonts/lunivo-office"

# Name → Prüfname : Größe : wozu
declare -A WAHL=(
  [opendyslexic]="OpenDyslexic:3,6 MB:Buchstaben mit Gewicht — gegen b/d und p/q"
  [lexend]="Lexend:240 KB:weit und luftig — für das Lesetempo"
  [atkinson]="Atkinson Hyperlegible:220 KB:unterscheidet I, l und 1 — für wenig Sehkraft"
)
REIHE=(opendyslexic lexend atkinson)

da_schon() {
    fc-list : family 2>/dev/null | grep -qi "^$1\|,$1" && return 0
    return 1
}

zeige_liste() {
    echo "Diese Schriften gibt es:"
    for name in "${REIHE[@]}"; do
        IFS=':' read -r pruef groesse wozu <<< "${WAHL[$name]}"
        if da_schon "$pruef"; then da="  ✓ liegt schon da"; else da=""; fi
        printf "  %-14s %-9s %-48s%s\n" "$name" "$groesse" "$wozu" "$da"
    done
    echo
    echo "Alle unter der SIL Open Font License 1.1."
}

entfernen() {
    if [ ! -d "$ZIEL" ]; then
        echo "Da ist nichts zu entfernen — $ZIEL gibt es nicht."
        exit 0
    fi
    rm -rf "$ZIEL"
    command -v fc-cache >/dev/null && fc-cache -f >/dev/null 2>&1 || true
    echo "Entfernt. Die Schriften stehen nicht mehr zur Wahl."
    exit 0
}

case "$1" in
    --liste) zeige_liste; exit 0 ;;
    --weg|--entfernen) entfernen ;;
    --alle) GEWUENSCHT=("${REIHE[@]}") ;;
    "") GEWUENSCHT=(opendyslexic) ;;
    *)  GEWUENSCHT=("$@") ;;
esac

for name in "${GEWUENSCHT[@]}"; do
    if [ -z "${WAHL[$name]}" ]; then
        echo "Unbekannt: $name" >&2
        zeige_liste
        exit 1
    fi
done

command -v curl >/dev/null || { echo "curl fehlt." >&2; exit 1; }
mkdir -p "$ZIEL"

# Der Lizenztext gehört dazu — er ist die Bedingung fürs Weitergeben.
cat > "$ZIEL/LIZENZ.txt" <<'LIZ'
Die Schriften in diesem Ordner stehen unter der
SIL Open Font License, Version 1.1 — https://openfontlicense.org

  OpenDyslexic            https://opendyslexic.org
                          https://github.com/antijingoist/opendyslexic
  Lexend                  https://www.lexend.com
                          https://github.com/googlefonts/lexend
  Atkinson Hyperlegible   https://brailleinstitute.org/freefont
                          https://github.com/googlefonts/atkinson-hyperlegible

Benutzen, weitergeben und verändern ist erlaubt, auch gewerblich. Die
Schriften dürfen nicht einzeln verkauft werden, und ein verändertes
Exemplar darf nicht unter dem Namen der Vorlage laufen.
LIZ

hole() {
    local wohin="$1" adresse="$2"
    if ! curl -fSL --progress-bar -o "$wohin" "$adresse"; then
        echo "Das ging nicht: $adresse" >&2
        return 1
    fi
}

for name in "${GEWUENSCHT[@]}"; do
    IFS=':' read -r pruef groesse wozu <<< "${WAHL[$name]}"
    if da_schon "$pruef"; then
        echo "$pruef liegt schon da."
        continue
    fi
    echo
    echo "$pruef — $groesse"
    echo "   $wozu"

    case "$name" in
        opendyslexic)
            paket="$ZIEL/.opendyslexic.zip"
            hole "$paket" "https://github.com/antijingoist/opendyslexic/releases/download/v0.91.12/opendyslexic-0.910.12-rc2-2019.10.17.zip"
            command -v unzip >/dev/null || { echo "unzip fehlt." >&2; exit 1; }
            # Nur die Schriftdateien, nicht der ganze Baum aus dem Paket.
            # Das „|| true" ist nötig: unzip meldet einen Fehler, wenn eines
            # der Muster nichts trifft — im Paket liegen nur .otf, kein
            # .ttf. Ohne das bräche das Skript hier ab, und die übrigen
            # Schriften kämen nie an.
            unzip -j -o -q "$paket" '*.otf' '*.ttf' -d "$ZIEL" 2>/dev/null || true
            rm -f "$paket"
            ;;
        lexend)
            hole "$ZIEL/Lexend.ttf" \
                 "https://raw.githubusercontent.com/googlefonts/lexend/main/fonts/lexend/variable/Lexend%5BHEXP%2Cwght%5D.ttf"
            ;;
        atkinson)
            for schnitt in Regular Bold Italic BoldItalic; do
                hole "$ZIEL/AtkinsonHyperlegible-$schnitt.ttf" \
                     "https://raw.githubusercontent.com/googlefonts/atkinson-hyperlegible/main/fonts/ttf/AtkinsonHyperlegible-$schnitt.ttf"
            done
            ;;
    esac
done

# Was aus einem Zip kommt, trägt die Rechte, die im Zip standen — und die
# waren hier 000. Eine Schrift, die niemand lesen darf, findet fontconfig
# nicht, und in der Liste stünde sie trotzdem nicht.
chmod 644 "$ZIEL"/*.otf "$ZIEL"/*.ttf 2>/dev/null || true

if command -v fc-cache >/dev/null; then
    fc-cache -f "$ZIEL" >/dev/null 2>&1 || fc-cache -f >/dev/null 2>&1 || true
fi

echo
echo "Fertig. Die Schriften stehen jetzt oben in der Schriftliste,"
echo "unter „Leichter zu lesen“."
echo
echo "Als Grundschrift für alles Neue: Optionen (F9) ▸ Schriftarten."
