<!--
SPDX-FileCopyrightText: 2026 Sebastian Espei <seblsebastian@aol.de>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# ics.tools – Kalender für deutsche Feiertage und Schulferien

Ein Open-Source-Projekt, das standardisierte ICS-Kalenderdateien für deutsche Feiertage und Schulferien bereitstellt.

## 📋 Projektbeschreibung

**ics.tools** automatisiert die Bereitstellung von Kalenderinformationen für alle deutschen Bundesländer. Das Projekt nutzt die Daten der [Open Holiday API](https://www.openholidaysapi.org/) als Grundlage, validiert diese manuell und stellt sie als ICS-Dateien zur Verfügung.

### Features

- Feiertage nach Bundesland (bundesweit + bundeslandspezifisch)
- Schulferien nach Bundesland
- Automatische Updates durch abonnierbare Kalender

## 🔄 Daten-Pipeline

1. **Fetch** (`01_fetch_*.py`) – Daten von Open Holidays API abrufen
2. **Override** – Manuelle Überprüfung und Anpassungen in `data/*/override/`
3. **Merge** (`02_merge_*.py`) – Daten + Overrides zusammenführen
4. **Generate** (`03_generate_*.py`) – ICS-Dateien erstellen

### Extras

- Kalenderwochen Kalender mit ganztätigen ``KWXX`` Einträgen jeden Montag 

## Lizenz

Dieses Projekt nutzt unterschiedliche Lizenzen für den Quellcode und die enthaltenen Daten:

*   **💻 Quellcode:** Der gesamte Programmcode steht unter der **GNU Affero General Public License v3 (AGPL-3.0)**. Der vollständige Lizenztext befindet sich in der Datei `LICENSE` im Hauptverzeichnis.
*   **📊 Daten:** Die Daten im Ordner `/data` (inklusive aller Anpassungen) basieren auf der Open Holiday API und stehen unter der **Open Database License (ODbL)**. Details dazu findest du in der `data/README.md`.

## 🏗️ Website-Generierung

Das Projekt nutzt **Jekyll** zur Umwandlung von Markdown in HTML:

```bash
python scripts/generate_page.py
jekyll build
```

Die Website wird automatisch über GitHub Actions deployed.

## 🚀 Verwendete Technologien

- **Python 3.X** – Skripte für die Daten-Pipeline
- **Jekyll** – Website-Generator (GitHub Pages)
- **Open Holidays API** – Datenquelle
- **ICS/iCalendar** (RFC 5545) – Kalenderformat
- **GitHub Actions** – CI/CD & Deployment

## 📊 Monitoring

Projekt-Status: [status.ics.tools](https://status.ics.tools)

## 🔗 Links

- 🌐 Website: [ics.tools](https://ics.tools)
- 📖 Repository: [github.com/ics-tools/ics.tools](https://github.com/ics-tools/ics.tools)
- 📋 Issues: [GitHub Issues](https://github.com/ics-tools/ics.tools/issues)

## 🤝 Contribution

Fehler gefunden? Idee für eine Verbesserung? 

→ [Issue erstellen](https://github.com/ics-tools/ics.tools/issues/new/choose)

---

**Open Source & Community-Driven**  
Copyright (C) 2021-2026 Sebastian Espei