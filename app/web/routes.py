# routes.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

INDEX_HTML = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RPI OPC UA Live</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    .tag-card { border-radius: 1rem; }
    .bool-on { background: #d1e7dd; }
    .bool-off { background: #f8d7da; }
    .tag-error { background: #f8d7da; }
    .mono { font-family: monospace; }
  </style>
</head>

<body class="bg-light">
<div class="container py-4">

  <div class="d-flex justify-content-between align-items-center mb-3">
    <div>
      <h1 class="h3 mb-1">Live Prozesswerte</h1>
      <div class="text-muted">Raspberry Pi · OPC UA Client → REST API</div>
    </div>
    <div class="text-end">
      <div class="badge bg-secondary" id="lastUpdate">Warte…</div>
    </div>
  </div>

  <div class="row g-3" id="cards"></div>

</div>

<script>

// ---------- GLOBAL ----------
const cards = document.getElementById("cards");
const lastUpdate = document.getElementById("lastUpdate");

// Speichert, für welche Tags das Schreiben im UI aktiviert ist
const outputEnabled = {};


// ---------- WRITE ----------
async function writeTag(name, value){
  try{
    const res = await fetch(`/api/tags/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: value })
    });

    if(!res.ok){
      throw new Error("HTTP " + res.status);
    }

    console.log("Write OK:", name, value);

    // Nach dem Schreiben direkt aktualisieren
    await refresh();

  }catch(e){
    console.error("Write Error:", e);
    alert("Fehler beim Schreiben!");
  }
}


// ---------- TOGGLE ----------
function toggleWrite(tagName){
  const checkbox = document.getElementById(`enable-${tagName}`);
  const writeDiv = document.getElementById(`write-${tagName}`);

  if(checkbox && writeDiv){
    const enabled = checkbox.checked;
    outputEnabled[tagName] = enabled;
    writeDiv.style.display = enabled ? "block" : "none";
  }
}


// ---------- HELPER ----------
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

function qualityBadgeClass(q){
  if (q === "good") return "bg-success";
  if (q === "written") return "bg-primary";
  if (q === "init") return "bg-secondary";
  return "bg-danger";
}


// ---------- CARD ----------
function makeCard(tag){

  const isBool = tag.type === "BOOL";
  const unit = tag.unit || "";
  const quality = tag.quality || "unknown";
  const displayName = tag.plc_name || tag.name || "-";
  const ts = tag.ts_client_ms ?? null;

  const checkboxId = `enable-${tag.name}`;
  const inputId = `input-${tag.name}`;
  const writeId = `write-${tag.name}`;

  let valueHtml = "";
  let cardClass = "";

  if (quality !== "good" && quality !== "written"){
    cardClass = "tag-error";
  }

  // ---------- BOOL ----------
  if(isBool){
    const on = !!tag.value;

    valueHtml = `
      <div>
        <div class="d-flex justify-content-between align-items-center mb-2">
          <span>${on ? "Ein" : "Aus"}</span>

          <div class="form-check">
            <input class="form-check-input"
              type="checkbox"
              id="${checkboxId}"
              ${outputEnabled[tag.name] ? "checked" : ""}
              onchange="toggleWrite('${tag.name}')">

            <label class="form-check-label small" for="${checkboxId}">
              Als Output verwenden
            </label>
          </div>
        </div>

        <div id="${writeId}" style="display:${outputEnabled[tag.name] ? "block" : "none"};">
          <button class="btn btn-sm btn-primary"
            onclick="writeTag('${tag.name}', ${!on})">
            Umschalten
          </button>
        </div>
      </div>
    `;

    if (quality === "good" || quality === "written"){
      cardClass = on ? "bool-on" : "bool-off";
    }

  } else {

    // ---------- NUMERIC ----------
    const n = Number(tag.value);

    valueHtml = `
      <div>
        <div class="mb-2">
          ${Number.isFinite(n) ? n.toFixed(2) : "-"} ${escapeHtml(unit)}
        </div>

        <div class="form-check mb-2">
          <input class="form-check-input"
            type="checkbox"
            id="${checkboxId}"
            ${outputEnabled[tag.name] ? "checked" : ""}
            onchange="toggleWrite('${tag.name}')">

          <label class="form-check-label small" for="${checkboxId}">
            Als Output verwenden
          </label>
        </div>

        <div id="${writeId}" style="display:${outputEnabled[tag.name] ? "block" : "none"};">
          <div class="d-flex gap-2">
            <input type="number"
              step="0.1"
              class="form-control form-control-sm"
              id="${inputId}"
              placeholder="Neuer Wert">

            <button class="btn btn-sm btn-primary"
              onclick="writeTag('${tag.name}', Number(document.getElementById('${inputId}').value))">
              Set
            </button>
          </div>
        </div>
      </div>
    `;
  }

  const description = tag.description
    ? `<div class="text-muted small mt-1">${escapeHtml(tag.description)}</div>`
    : "";

  return `
    <div class="col-12 col-md-6 col-lg-4">
      <div class="card tag-card shadow-sm ${cardClass}">
        <div class="card-body">

          <div class="d-flex justify-content-between align-items-start">
            <div>
              <div class="fw-semibold">${escapeHtml(displayName)}</div>
              <div class="text-muted small">
                ${escapeHtml(tag.type)}${unit ? " · " + escapeHtml(unit) : ""}
              </div>
              ${description}
            </div>

            <span class="badge ${qualityBadgeClass(quality)}">
              ${escapeHtml(quality)}
            </span>
          </div>

          <div class="mt-3">
            ${valueHtml}
          </div>

          <div class="text-muted small mt-2">
            ts: ${fmtTime(ts)}
          </div>

        </div>
      </div>
    </div>
  `;
}


// ---------- REFRESH ----------
async function refresh(){
  try{
    const res = await fetch("/api/tags", { cache: "no-store" });

    if(!res.ok){
      throw new Error("HTTP " + res.status);
    }

    const data = await res.json();
    const tags = Array.isArray(data.tags) ? data.tags : [];

    cards.innerHTML = tags.map(makeCard).join("");

    lastUpdate.className = "badge bg-success";
    lastUpdate.textContent = "Update: " + fmtTime(data.ts);

  }catch(e){
    console.error("Refresh Error:", e);
    lastUpdate.className = "badge bg-danger";
    lastUpdate.textContent = "Fehler beim Laden";
  }
}


// ---------- LOOP ----------
refresh();
setInterval(refresh, 500);

</script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)