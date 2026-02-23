### NEU ###
## Starten der Web oberfläche ##
uv run uvicorn main:app --host 0.0.0.0 --port 8000






### ALT ###
## Starten ##
uvicorn main:app --host 0.0.0.0 --port 8000

## Lokal starten ##
uv run uvicorn main:app --host 0.0.0.0 --port 8000

## Im Browser öffnen ##
http://<IP-DEINES-RPI>:8000/
http://<IP-DEINES-RPI>:8000/api/tags
http://localhost:8000
http://localhost:8000/api/tags

## QUIT ##
ctl + c+

## IP Raspberry ##
10.9.229.187