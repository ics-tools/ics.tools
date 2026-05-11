# ics.tools – Kalender für deutsche Feiertage und Schulferien

Ein Open-Source-Projekt, das standardisierte ICS-Kalenderdateien für deutsche Feiertage und Schulferien bereitstellt.

## 📋 Projektbeschreibung

**ics.tools** automatisiert die Bereitstellung von Kalenderinformationen für alle deutschen Bundesländer. Das Projekt bezieht Daten von der Open Holidays API, validiert sie manuell und stellt sie als ICS-Dateien zur Verfügung.

### Features

- Feiertage nach Bundesland (bundesweit + bundeslandspezifisch)
- Schulferien nach Bundesland
- Automatische Updates durch abonnierbare Kalender

## 🔄 Daten-Pipeline

1. **Fetch** (`01_fetch_*.py`) – Daten von Open Holidays API abrufen
2. **Override** – Manuelle Überprüfung und Anpassungen in `data/*/override/`
3. **Merge** (`02_merge_*.py`) – Daten + Overrides zusammenführen
4. **Generate** (`03_generate_*.py`) – ICS-Dateien erstellen

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
