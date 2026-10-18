#!/usr/bin/env python3
"""Liest oberflaeche/daten/vorlagenmuster.js (mit Node) und schreibt native_qt/resources/vorlagenmuster.json:
[{id, name, beschreibung, zeilen}] — die zehn mitgelieferten Gerüste (Brief, Bewerbung, Lebenslauf …)."""
import json
import os
import subprocess

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
quelle = os.path.join(WURZEL, "oberflaeche/daten/vorlagenmuster.js")
js = ("const fs=require('fs'),vm=require('vm');"
      f"const q=fs.readFileSync({json.dumps(quelle)},'utf8');"
      "const v=vm.runInNewContext(q+';VORLAGENMUSTER');"
      "console.log(JSON.stringify(v.map(([id,name,beschreibung,zeilen])=>({id,name,beschreibung,zeilen}))));")
daten = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
ziel = os.path.join(WURZEL, "native_qt/resources/vorlagenmuster.json")
json.dump(daten, open(ziel, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(daten), "Gerüste →", ziel)
