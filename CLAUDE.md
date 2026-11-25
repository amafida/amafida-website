# amafida.de – Hinweise für Claude

Statische Website auf GitHub Pages (Domain amafida.de, Datei `CNAME`). Keine Build-Schritte: Jede Seite ist eine eigenständige `index.html` mit eingebetteten Schriften.

## Seiten

- `/` – amafida, die Dachmarke. Leitet zu scoledo und Civenio weiter.
- `/scoledo/` – Startseite der Schulmaterial-Marke scoledo.
- `/scoledo/materialien/` – Katalog aller Materialien. **Quelle der Wahrheit** für Materialien und alle Zahlen.
- `/links/` – kurze Seite für den Link in der Instagram-Bio von @scoledo.de: Neu, Gratis, Pakete.
- `/qualitaet/`, `/impressum/`, `/datenschutz/`.
- Cover liegen unter `/links/*.jpg` (240 × 340 px).

## Arbeitsweise

- Änderungen auf einem Branch, dann Pull Request. Der Nutzer mergt selbst.
- Gestaltung nach dem scoledo-Design-System (Artefakt „scoledo“): H1 und H2 in Fraunces kursiv, Kartentitel in Outfit, Text in Plus Jakarta Sans. Keine Emojis im Web.
- Keine externen Requests, keine Cookies, kein Tracking: Schriften und Bilder bleiben lokal.
- Neue Seiten in `sitemap.xml` eintragen.

## Aktualitäts-Check: vor jedem Commit

1. `python3 .github/scripts/aktualitaet.py --fix` ausführen. Das Skript zählt die Materialien im Katalog, setzt alle Zahlen im Text und die Abschnittszähler neu und aktualisiert das ©-Jahr.
2. Was es nicht selbst beheben kann, vor dem Commit klären und dem Nutzer nennen:
   - abgelaufene saisonale Inhalte (`data-gueltig-bis`): austauschen oder Datum verlängern,
   - Unterschiede zwischen `/links/` und Katalog bei Neu und Gratis,
   - Hinweise auf vergangene Jahreszahlen in Titeln (z. B. „Mein Jahr 2026“ im Jahr 2027).
3. Regeln für neue Inhalte:
   - Neue Materialien zuerst in den Katalog, bei Neu oder Gratis zusätzlich auf `/links/`.
   - Jede Zahl im Fließtext, die sich aus dem Katalog ergibt, als `<span data-zaehle="NAME">ZAHL</span>` schreiben. Zähler: `neu`, `pakete`, `kunst`, `gratis`, `sachunterricht`, `werkstaetten`, `kunststunden`, `alle`.
   - In Buttons und Kartenzeilen (`.btn`, `.go`, `.chip`, alles mit `display:flex`) Zahl und Text gemeinsam in ein eigenes `<span>` packen, sonst verschwinden die Leerzeichen: `<a class="btn"><span>Alle <span data-zaehle="gratis">9</span> Gratis-Materialien</span></a>`.
   - Vor dem Commit geänderte Seiten bei 390 und 1280 px rendern und ansehen, nicht nur den Quelltext prüfen.
   - Saisonales mit `data-gueltig-bis="JJJJ-MM-TT"` am Link (`<a …>`) markieren.

Derselbe Check läuft auf GitHub bei jedem Pull Request, bei jedem Push auf main und jeden Montagmorgen (`.github/workflows/aktualitaet.yml`).
