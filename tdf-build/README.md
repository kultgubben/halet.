# TdF 2026 – byggpipeline

`tdf-2026.html` genereras från `tdf_template.html` + fyra data-JSON:
`route.json` (hela rutten), `results.json` (etappresultat), `standings.json`
(alla klassementen), `startlist.json` (lag/åkare/nördstatistik).

Uppdatering efter en etapp:
1. Uppdatera `results.json` (nytt etappobjekt + `lastCompletedStage`) och
   `standings.json` (nya tabeller + `afterStage`, abandons, combativity).
   Svenska med korrekta å/ä/ö i `summary`/`reason`. Lagnamn normaliseras
   automatiskt av byggskriptet.
2. Kör `python3 tdf-build/build_tdf.py` → skriver om `tdf-2026.html` i repo-roten.
3. Publicera om artifakten (samma fil → samma URL):
   https://claude.ai/code/artifact/f5af514d-856a-4805-9808-d6eeba68a299
4. Committa + pusha till claude/tdf-2026-stats-app-76xkal.
