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
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
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

  <div class="mt-4 text-muted small mono">
    API: <span>/api/tags</span> · <span>/api/tags/&lt;name&gt;</span>
  </div>
</div>

<script>
const cards = document.getElementById("cards");
const lastUpdate = document.getElementById("lastUpdate");

function fmtTime(ms){
  if (ms === null || ms === undefined) return "-";
  const n = Number(ms);
  if (!Number.isFinite(n)) return "-";
  const d = new Date(n);
  if (Number.isNaN(d.getTime())) return "-";
  return d.toLocaleTimeString();
}

function escapeHtml(value){
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function qualityBadgeClass(quality){
  if (quality === "good") return "bg-success";
  if (quality === "init") return "bg-secondary";
  if (quality === "set-via-rest") return "bg-primary";
  return "bg-danger";
}

function makeCard(tag){
  const isBool = tag.type === "BOOL";
  const unit = tag.unit || "";
  const quality = tag.quality || "unknown";
  const displayName = tag.plc_name || tag.name || "-";
  const ts = tag.ts_client_ms ?? null;

  let valueHtml = "";
  let cardClass = "";

  if (quality !== "good" && quality !== "set-via-rest") {
    cardClass = "tag-error";
  }

  if(isBool){
    const on = !!tag.value;
    valueHtml = on ? "Ein" : "Aus";
    if (quality === "good" || quality === "set-via-rest") {
      cardClass = on ? "bool-on" : "bool-off";
    }
  } else {
    const n = Number(tag.value);
    valueHtml = Number.isFinite(n)
      ? n.toFixed(2) + (unit ? " " + unit : "")
      : escapeHtml(tag.value) + (unit ? " " + unit : "");
  }

  const description = tag.description ? `<div class="text-muted small mt-1">${escapeHtml(tag.description)}</div>` : "";

  return `
    <div class="col-12 col-md-6 col-lg-4">
      <div class="card tag-card shadow-sm ${cardClass}">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <div class="fw-semibold">${escapeHtml(displayName)}</div>
              <div class="text-muted small">${escapeHtml(tag.type || "-")}${unit ? " · " + escapeHtml(unit) : ""}</div>
              ${description}
            </div>
            <span class="badge ${qualityBadgeClass(quality)}">${escapeHtml(quality)}</span>
          </div>
          <div class="display-6 mt-3">${valueHtml}</div>
          <div class="text-muted small mt-2">ts: ${fmtTime(ts)}</div>
        </div>
      </div>
    </div>
  `;
}

async function refresh(){
  try{
    const res = await fetch("/api/tags", { cache: "no-store" });
    if(!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    const tags = Array.isArray(data.tags) ? data.tags : [];
    cards.innerHTML = tags.map(makeCard).join("");

    lastUpdate.className = "badge bg-success";
    lastUpdate.textContent = "Update: " + fmtTime(data.ts);
  }catch(e){
    lastUpdate.className = "badge bg-danger";
    lastUpdate.textContent = "Fehler beim Laden";
  }
}

refresh();
setInterval(refresh, 800);
</script>
</body>
</html>
"""

@router.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)