# RPI OPC UA Client + Web UI 
## Beschreibung
Diese Anwendung liest Daten von einer Siemens S7-1500 CPU, die einen OPC UA Server bereitstellt.

Die Daten werden über eine Subscription vom Raspberry Pi als OPC UA Client empfangen und im Backend verarbeitet.

Anschließend werden die Daten über eine REST API (HTTP) bereitgestellt und von einer Weboberfläche im Browser visualisiert.

Zusätzlich werden angezeigt:

    aktuelle Prozesswerte
    Zeitstempel der Werte
    Verbindungsstatus zum OPC-UA Server

Dadurch können nach Erweiterungen auch mehrere Anlagen verknüpft Visualisiert und die Daten zentral gesammelt auf einem Server bereitgestellt werden.

### Setup
Auf dem Raspberry PI ist Raspberry OS installiert und der Code wurde vollständig in VS Code in Python geschrieben. Die notwenigen Bibliotheken sind unter "requirements.txt" zu finden.
Die Datei auf GitHub public hochgeladen, damit es vom RPI aus geclont werden kann: 
https://github.com/felixsteffel/SmartView-OPC-RPI
Branch: main


### Starten der Anwendung
uv run uvicorn main:app --host 0.0.0.0 --port 8000
Anmeldedaten: ADMIN - 9865

### Beenden
Ctrl + C


## Zugriff im Browser
### Lokal
http://localhost:8000
http://localhost:8000/api/tags

### Im Netzwerk (Raspberry Pi)
http://10.9.229.187:8000/
http://10.9.229.187:8000/api/tags

### Netzwerk / Geräte
Gerät	IP-Adresse
Raspberry Pi	10.9.229.187
SPS (S7-1500)	192.168.3.12
OPCUA Endpoint opc.tcp://192.168.3.12:4840


### Hinweise
Die Daten werden per Subscription aktualisiert, der Server sendet also aktiv die Daten an den Client.
Die Weboberfläche aktualisiert sich automatisch.

## Architektur
```
SPS (S7-1500)
   │
   │ OPC UA (NodeIds + Values)
   ▼
Raspberry Pi (OpcUaReader)
   │
   │ Polling
   ▼
CURRENT_TAGS (In-Memory Store)
   │
   ▼
FastAPI (/api/tags)
   │
   ▼
Web UI (Browser)
```

## Team
Felix Steffel
Johannes Scharrer
MTV2426B - SFE

## Lizenz
Für TIA sowie den OPC-UA Server in TIA wurden Lizenzen der Schule genutzt.
