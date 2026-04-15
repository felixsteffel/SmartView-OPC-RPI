# routes.py

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from ..config import settings

router = APIRouter()

# Oberfläche mit Login-Schutz, um die Tag-Daten anzuzeigen und zu steuern.
LOGIN_HTML = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Login</title>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #111;
      font-family: Arial, Helvetica, sans-serif;
      color: white;
    }
    .box {
      width: min(380px, 92vw);
      padding: 28px;
      border-radius: 16px;
      background: rgba(255,255,255,0.08);
      box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }
    h1 {
      margin: 0 0 18px;
      font-size: 24px;
    }
    .muted {
      color: #ccc;
      margin-bottom: 18px;
      font-size: 14px;
    }
    input {
      width: 100%;
      padding: 12px;
      margin: 0 0 12px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.18);
      background: rgba(255,255,255,0.08);
      color: white;
      box-sizing: border-box;
    }
    button {
      width: 100%;
      padding: 12px;
      border: 0;
      border-radius: 10px;
      background: #2b6fff;
      color: white;
      font-weight: 700;
      cursor: pointer;
    }
    .error {
      background: rgba(180, 20, 20, 0.85);
      padding: 10px 12px;
      border-radius: 10px;
      margin-bottom: 12px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <form class="box" method="post" action="/login">
    <h1>Anmeldung</h1>
    <div class="muted">Bitte Username und Passwort eingeben.</div>
    __ERROR_HTML__
    <input type="text" name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Passwort" required>
    <button type="submit">Login</button>
  </form>
</body>
</html>
"""

# Nutzeroberfläche mit Panels, die die aktuellen Werte der Tags anzeigen
INDEX_HTML = r"""
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RPI OPC UA Live</title>
  <style>
    :root {
      --panel-border: rgba(255, 255, 255, 0.18);
      --panel-text: #f4f4f4;
      --shadow: 0 10px 28px rgba(0,0,0,0.35);
      --radius: 13px;
    }

    * { box-sizing: border-box; }

    html, body {
      margin: 0;
      padding: 0;
      background: #111;
      font-family: Arial, Helvetica, sans-serif;
      color: white;
    }

    .page {
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 12px;
      background: #111;
    }

    .anlage {
      position: relative;
      width: min(1400px, 100vw);
      aspect-ratio: 16 / 9;
      background-image: url('/static/Hintergrund.png');
      background-size: contain;
      background-repeat: no-repeat;
      background-position: center;
      overflow: hidden;
    }

    .panel {
      position: absolute;
      border: 2px solid var(--panel-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      color: var(--panel-text);
      user-select: none;
      overflow: hidden;
    }

    .panel.small {
      width: 20.8%;
      min-height: 7.2%;
      padding: 0.85% 1.6%;
      display: flex;
      align-items: center;
      justify-content: flex-start;
    }

    .panel.bool-true {
      background: linear-gradient(180deg, rgba(34, 185, 77, 0.94), rgba(17, 130, 46, 0.94));
    }

    .panel.bool-false {
      background: linear-gradient(180deg, rgba(210, 39, 39, 0.94), rgba(150, 14, 14, 0.94));
    }

    .panel.pressure {
      width: 14.4%;
      min-height: 12.8%;
      padding: 0.95% 1.1%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: stretch;
      text-align: center;
      background: rgba(8, 8, 10, 0.88);
    }

    .desc-main {
      font-size: clamp(13px, 1.08vw, 24px);
      font-weight: 700;
      line-height: 1.08;
      margin-bottom: 3px;
    }

    .plc-sub {
      font-size: clamp(9px, 0.72vw, 14px);
      line-height: 1.12;
      opacity: 0.96;
    }

    .pressure-value-row {
      display: flex;
      align-items: baseline;
      justify-content: center;
      gap: 3%;
      line-height: 1;
      margin-top: 8px;
    }

    .pressure-value {
      font-size: clamp(22px, 3.3vw, 62px);
      font-weight: 700;
      letter-spacing: 0.02em;
    }

    .pressure-unit {
      font-size: clamp(13px, 1.75vw, 30px);
      font-weight: 600;
      color: #f1f1f1;
    }

    .write-row {
      margin-top: 10px;
      display: flex;
      gap: 8px;
      justify-content: center;
      align-items: center;
      flex-wrap: wrap;
    }

    .write-row button {
      padding: 6px 12px;
      border: 0;
      border-radius: 8px;
      background: #2b6fff;
      color: white;
      font-weight: 600;
      cursor: pointer;
    }

    .panel-content-left {
      width: 100%;
    }

    .panel-content-center {
      width: 100%;
      text-align: center;
    }

    .meta {
      position: absolute;
      left: 10.0%;
      bottom: 1.4%;
      padding: 8px 12px;
      background: rgba(0,0,0,0.45);
      border-radius: 10px;
      font-size: clamp(10px, 0.8vw, 14px);
      color: #ddd;
      z-index: 5;
    }

    .meta.error {
      background: rgba(150, 20, 20, 0.75);
      color: white;
    }

    .quality {
      position: absolute;
      right: 10.0%;
      bottom: 1.4%;
      padding: 8px 12px;
      background: rgba(0,0,0,0.45);
      border-radius: 10px;
      font-size: clamp(10px, 0.8vw, 14px);
      color: #ddd;
      z-index: 5;
    }

    .alarm {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(200, 0, 0, 0.96);
      color: white;
      padding: 28px 52px;
      border-radius: 20px;
      border: 3px solid white;
      text-align: center;
      box-shadow: 0 0 40px rgba(255,0,0,0.7);
      z-index: 999;
    }

    .alarm-title {
      font-size: clamp(26px, 2.6vw, 46px);
      font-weight: 800;
      line-height: 1.1;
      margin-bottom: 10px;
    }

    .alarm-text {
      font-size: clamp(18px, 1.5vw, 28px);
      font-weight: 600;
      line-height: 1.2;
    }

    .hidden {
      display: none;
    }
  </style>
</head>
<body>
<div class="page">
  <div class="anlage">

    <div id="card-zyl-ausgefahren" class="panel small" style="left:10.0%; top:14.6%;"></div>
    <div id="card-zyl-eingefahren" class="panel small" style="left:10.0%; top:5.8%;"></div>

    <div id="card-zyl-ausfahren" class="panel small" style="left:10.0%; top:24.5%;"></div>
    <div id="card-zyl-einfahren" class="panel small" style="left:10.0%; top:37.6%;"></div>

    <div id="card-druck" class="panel pressure" style="right:9.5%; top:5.8%;"></div>

    <div id="card-teil-erkannt" class="panel small" style="left:10.0%; bottom:7.8%;"></div>
    <div id="card-kein-teil" class="panel small" style="right:9.5%; bottom:7.8%;"></div>

    <div id="meta" class="meta">Warte auf Daten…</div>
    <div id="quality" class="quality">Status: -</div>

    <div id="alarm-overlay" class="alarm hidden">
      <div class="alarm-title">⚠ WARNUNG ⚠</div>
      <div class="alarm-text">Druck größer als 7 bar</div>
    </div>
  </div>
</div>

<script>
  function fmtTime(ms){
    if (!ms) return "-";
    const d = new Date(Number(ms));
    return isNaN(d.getTime()) ? "-" : d.toLocaleTimeString();
  }

  function escapeHtml(value){
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getTagMap(tags){
    const map = {};
    for(const t of tags){
      map[t.name] = t;
    }
    return map;
  }

  function displayDescription(tag, fallback=""){
    return escapeHtml(tag?.description || fallback || "-");
  }

  function displayPlcName(tag, fallback=""){
    return escapeHtml(tag?.plc_name || tag?.name || fallback || "-");
  }

  async function writeTag(name, value){
    try{
      const res = await fetch(`/api/tags/${encodeURIComponent(name)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value })
      });

      let payload = null;
      try {
        payload = await res.json();
      } catch {
        payload = null;
      }

      if(!res.ok){
        const detail = payload?.detail || `HTTP ${res.status}`;
        throw new Error(detail);
      }

      await refresh();
    }catch(e){
      console.error("Write Error:", e);
      alert("Fehler beim Schreiben: " + (e?.message || e));
    }
  }

  function renderBoolPanel(containerId, tag, fallbackDesc=""){
    const el = document.getElementById(containerId);
    if(!el) return;

    const value = !!(tag && tag.value);

    el.className = "panel small " + (value ? "bool-true" : "bool-false");
    el.innerHTML = `
      <div class="panel-content-left">
        <div class="desc-main">${displayDescription(tag, fallbackDesc)}</div>
        <div class="plc-sub">${displayPlcName(tag)}</div>
      </div>
    `;
  }

  function renderWriteBoolPanel(containerId, tag, fallbackDesc="", writeValue=true){
    const el = document.getElementById(containerId);
    if(!el) return;

    const value = !!(tag && tag.value);
    const tagName = tag?.name || "";

    el.className = "panel small " + (value ? "bool-true" : "bool-false");
    el.innerHTML = `
      <div class="panel-content-center">
        <div class="desc-main">${displayDescription(tag, fallbackDesc)}</div>
        <div class="plc-sub">${displayPlcName(tag)}</div>

        <div class="write-row">
          <button onclick="writeTag('${tagName}', ${writeValue})">
            Schreiben
          </button>
        </div>
      </div>
    `;
  }

  function renderPressure(containerId, tag, fallbackDesc="Druck"){
    const el = document.getElementById(containerId);
    if(!el) return;

    let value = "-";
    let unit = escapeHtml(tag?.unit || "bar");

    if(tag){
      const n = Number(tag.value);
      value = Number.isFinite(n) ? n.toFixed(1) : escapeHtml(tag.value);
    }

    el.innerHTML = `
      <div class="desc-main">${displayDescription(tag, fallbackDesc)}</div>
      <div class="plc-sub">${displayPlcName(tag)}</div>

      <div class="pressure-value-row">
        <div class="pressure-value">${value}</div>
        <div class="pressure-unit">${unit}</div>
      </div>
    `;
  }

  function checkPressureAlarm(tag){
    const alarm = document.getElementById("alarm-overlay");

    if(!alarm){
      return;
    }

    if(!tag){
      alarm.classList.add("hidden");
      return;
    }

    const value = Number(tag.value);

    if(Number.isFinite(value) && value > 7){
      alarm.classList.remove("hidden");
    } else {
      alarm.classList.add("hidden");
    }
  }

  function updateMeta(tags, serverTs){
    const meta = document.getElementById("meta");
    const quality = document.getElementById("quality");

    const qualities = tags.map(t => t.quality).filter(Boolean);
    const unique = [...new Set(qualities)];
    const hasBad = unique.some(q => !["good", "written", "init"].includes(q));

    meta.className = hasBad ? "meta error" : "meta";
    meta.textContent = `Update: ${fmtTime(serverTs)}`;
    quality.textContent = `Status: ${unique.join(", ") || "-"}`;
  }

  async function refresh(){
    try{
      const res = await fetch("/api/tags", { cache: "no-store" });
      if(!res.ok) throw new Error("HTTP " + res.status);

      const data = await res.json();
      const tags = Array.isArray(data.tags) ? data.tags : [];
      const map = getTagMap(tags);

      renderBoolPanel(
        "card-zyl-ausgefahren",
        map["c1_bg2_front_position"],
        "Zylinder ausgefahren"
      );

      renderBoolPanel(
        "card-zyl-eingefahren",
        map["c1_bg1_rear_position"],
        "Zylinder eingefahren"
      );

      renderWriteBoolPanel(
        "card-zyl-ausfahren",
        map["Zylinder ausfahren"],
        "Zylinder ausfahren",
        true
      );

      renderWriteBoolPanel(
        "card-zyl-einfahren",
        map["Zylinder einfahren"],
        "Zylinder einfahren",
        true
      );

      renderPressure(
        "card-druck",
        map["analog_druck_out"],
        "Druck"
      );

      renderBoolPanel(
        "card-teil-erkannt",
        map["g1_bg1_left_sensor"],
        "optischer Sensor Links"
      );

      renderBoolPanel(
        "card-kein-teil",
        map["g1_bg2_right_sensor"],
        "optischer Sensor Rechts"
      );

      checkPressureAlarm(map["analog_druck_out"]);
      updateMeta(tags, data.ts);

    }catch(e){
      console.error("Refresh Error:", e);
      const meta = document.getElementById("meta");
      meta.className = "meta error";
      meta.textContent = "Fehler beim Laden";

      const alarm = document.getElementById("alarm-overlay");
      if(alarm){
        alarm.classList.add("hidden");
      }
    }
  }

  refresh();
  setInterval(refresh, 500);
</script>
</body>
</html>
"""

# Hilfsfunktion, um zu prüfen, ob der Nutzer eingeloggt ist
def is_logged_in(request: Request) -> bool:
    return request.session.get("authenticated") is True

# Hilfsfunktion, um den Login-Status zu erzwingen
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_logged_in(request):
        return RedirectResponse(url="/", status_code=303)
    return HTMLResponse(LOGIN_HTML.replace("__ERROR_HTML__", ""))

# Endpoint, um die Login-Daten zu verarbeiten und die Session zu setzen
@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == settings.WEB_USERNAME and password == settings.WEB_PASSWORD:
        request.session["authenticated"] = True
        request.session["username"] = username
        return RedirectResponse(url="/", status_code=303)

    error_html = '<div class="error">Ungültiger Username oder Passwort.</div>'
    return HTMLResponse(
        LOGIN_HTML.replace("__ERROR_HTML__", error_html),
        status_code=401
    )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=303)
    return HTMLResponse(INDEX_HTML)