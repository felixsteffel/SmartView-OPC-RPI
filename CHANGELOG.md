09.02.2026
An der CPU:
1. OPC UA Server aktivieren
    1) Prüfen: CPU kann OPC UA Server
        • S7-1500: meist integriert (je nach CPU/Firmware)
        • S7-1200: nur bestimmte Firmware/Modelle unterstützen OPC UA
    Wenn der Menüpunkt OPC UA im TIA nicht auftaucht, fehlt oft Support/Option oder die Firmware/CPU kann’s nicht.
    
2. Variablen/DBs für OPC UA freigeben (Tags publizieren)
    2) OPC UA Server in der CPU aktivieren
    TIA Portal → Geräte & Netze → CPU → Eigenschaften
        • OPC UA (oder “OPC UA Server”) aktivieren
        • Endpoint/Port prüfen (Standard: opc.tcp://<cpu-ip>:4840)
        • Servername/Anwendung (optional) setzen
    
3. Security/Benutzer/Zertifikate so einstellen, dass dein RPi lesen darf
    3) Variablen für OPC UA freigeben (die wichtigsten Schritte)
    OPC UA liefert nicht automatisch alle DB-Werte – du musst sie publizieren:
    Variante A (typisch/empfohlen): über “OPC UA Server Interface”
        • CPU → OPC UA → Server-Schnittstelle / Address Space
        • Dort Tags/Variablen hinzufügen, die du lesen willst:
            ○ REAL, BOOL aus DBs, Merker, Ein-/Ausgänge usw.
        • Danach werden sie im OPC UA-Adressraum sichtbar → du bekommst NodeIds
    Variante B: “Symbolische” Freigabe (je nach Projekt/CPU)
        ○ Sicherstellen, dass die Variablen symbolisch erreichbar sind und nicht optimiert blockiert werden (siehe Punkt 4)


23.02.2026

    - Desktop-Verbindung über VNC kabellos auf RPI herstellen
    - VS Code auf RPI installieren
    - Code für Server Frontend (HTML) sowie und API - Schnittstelle für Datenaustausch hinzufügen
    - Git auf Entwicklungs-PC installiert und von VSCode in Github geladen:
        ○ Venv nicht mit hochladen, da es eine Virtuelle Umgebung ist (.gitignore erstellt)
        ○ Commit hinzufügen: git add .
        ○ Commit erstellen: git commit -m "Initial commit"
        ○ Remote Pfad hinzufügen: git remote add origin https://github.com/felixsteffel/SmartView-OPC-RPI.git
        ○ Branch auf Main setzten: git branch -M main
        ○ Hochladen: git push -u origin main
        
        ○ Updates über: 
        git add .
        git commit -m "Update"
        git push
        
        ○ Neuer Branch:
        git checkout -b feature/opcua-fix
        git add .
        git commit -m "Fix OPC UA NodeIds"
        git push -u origin feature/opcua-fix


02.03.2026
    - Überprüfen, ob Python installiert ist (RPI) --> Ja
    - Überprüfen, ob GIT installiert ist (RPI)  --> Ja
    - Projekt aus Git holen:   
    cd ~
    git clone https://github.com/felixsteffel/SmartView-OPC-RPI.git
    cd SmartView-OPC-RPI
    - Uv installieren:
    curl -Ls https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    - Virtuelle umgebung starten
    curl -Ls https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
    - Starten: uv run uvicorn main:app --host 0.0.0.0 --port 8000

23.03.2026
    - debug skript, um NodeIds herauszufinden (debug2.py)
    - Verbindung zur SPS hergestellt, NodeIds angepasst (2-->3)
    - Anpassungen Druckumrechnung

13.04.2026
    - Subsciption statt Polling abgeändert
    - Backend für "Write" mit eingebaut, um ausgänge auch schreiben zu können
    - Readme überarbeitet

15.04.2026
    - Hintergrund der Weboberfläche geändert, sodass das Förderband als Grafik vorhanden ist
    - Anmeldung über Session-based Authentication (Bleibt in den Cookies gespeichert)
    - Grenzwert bei 7 bar führt zu einer Fehlermeldung