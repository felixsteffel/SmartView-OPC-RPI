# Changelog

Alle wichtigen Änderungen und Fortschritte des Projekts werden hier dokumentiert.

---

## [2026-04-15]

### ✨ Features
- Weboberfläche visuell überarbeitet:
  - Hintergrundbild der Anlage integriert (Förderband)
  - Panels direkt auf der Grafik positioniert
- Session-basierte Authentifizierung hinzugefügt:
  - Login mit Username & Passwort
  - Session bleibt im Browser (Cookies) gespeichert
- Grenzwertüberwachung implementiert:
  - Warnmeldung bei Druck > 7 bar (Overlay im UI)

---

## [2026-04-13]

### 🔧 Änderungen
- Kommunikation von Polling auf **OPC UA Subscription** umgestellt
  - Echtzeit-Updates statt zyklischem Abfragen

### ✨ Features
- Schreibfunktion (Write) implementiert:
  - Werte können über Weboberfläche an die SPS gesendet werden
  - Integration in REST API (`POST /api/tags/{name}`)

### 📝 Dokumentation
- README überarbeitet und erweitert

---

## [2026-03-23]

### 🔧 Änderungen
- Debug-Skript (`debug2.py`) erstellt zur Analyse von NodeIds
- OPC UA Verbindung erfolgreich hergestellt
- NodeIds angepasst (`ns=2` → `ns=3`)
- Umrechnung für Druckwerte korrigiert (DWORD → FLOAT)

---

## [2026-03-02]

### ⚙️ Setup Raspberry Pi
- Python und Git überprüft und bestätigt
- Projekt von GitHub geklont:
  - `git clone https://github.com/felixsteffel/SmartView-OPC-RPI.git`
- `uv` installiert und virtuelle Umgebung eingerichtet
- Anwendung gestartet mit:
  - `uv run uvicorn main:app --host 0.0.0.0 --port 8000`

---

## [2026-02-23]

### 🖥️ Entwicklung & Infrastruktur
- VNC-Verbindung zum Raspberry Pi eingerichtet
- VS Code auf dem RPi installiert

### ✨ Features
- Backend (FastAPI) erstellt:
  - REST API für Tags
- Frontend entwickelt:
  - HTML-basierte Visualisierung der Prozessdaten

### 🔧 Git Setup
- Repository erstellt und initialisiert
- `.gitignore` hinzugefügt (virtuelle Umgebung ausgeschlossen)

### 📦 Git Workflow
- Initialer Commit:
  - `git add .`
  - `git commit -m "Initial commit"`
- Remote Repository verbunden:
  - `git remote add origin https://github.com/felixsteffel/SmartView-OPC-RPI.git`
  - `git branch -M main`
  - `git push -u origin main`

### 🔄 Updates
- `git add .`
- `git commit -m "Update"`
- `git push`

### 🌿 Feature Branch
- `git checkout -b feature/opcua-fix`
- `git add .`
- `git commit -m "Fix OPC UA NodeIds"`
- `git push -u origin feature/opcua-fix`

---

## [2026-02-09]

### ⚙️ OPC UA Einrichtung (TIA Portal)

#### 1. OPC UA Server aktivieren
- CPU muss OPC UA unterstützen:
  - S7-1500: meist integriert
  - S7-1200: abhängig von Modell/Firmware
- Aktivierung im TIA Portal:
  - CPU → Eigenschaften → OPC UA Server aktivieren
  - Endpoint prüfen:
    - `opc.tcp://<cpu-ip>:4840`

#### 2. Variablen freigeben (Adressraum)
- OPC UA Server Interface konfigurieren:
  - Tags manuell hinzufügen (DB, Merker, Ein-/Ausgänge)
- Alternativ:
  - Symbolische Variablen freigeben (abhängig von CPU)

#### 3. Sicherheit konfigurieren
- Benutzer, Rechte und Zertifikate definieren
- Zugriff für Raspberry Pi erlauben