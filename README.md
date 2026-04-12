### RPI OPC UA Client + Web UI 
## Beschreibung

Diese Anwendung liest Daten von einer Siemens S7-1500 CPU, die einen OPC-UA Server bereitstellt.

Die Daten werden zyklisch (Polling) von einem Raspberry Pi gelesen und über eine Weboberfläche dargestellt.

Zusätzlich werden angezeigt:

    aktuelle Prozesswerte
    Zeitstempel der Werte
    Verbindungsstatus zum OPC-UA Server

## Starten der Anwendung
uv run uvicorn main:app --host 0.0.0.0 --port 8000

## Beenden
Ctrl + C
Zugriff im Browser

## Lokal
http://localhost:8000
http://localhost:8000/api/tags

## Im Netzwerk (Raspberry Pi)
http://10.9.229.187:8000/
http://10.9.229.187:8000/api/tags

## Netzwerk / Geräte
Gerät	IP-Adresse
Raspberry Pi	10.9.229.187
SPS (S7-1500)	192.168.3.12
HMI	192.168.3.14

## Hinweise
Die Daten werden per Polling aktualisiert (kein OPC-UA Subscription).
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
