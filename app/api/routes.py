# app/api/routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..store import CURRENT_TAGS, now_ms
from ..config import TAGS_CONFIG

router = APIRouter(prefix="/api", tags=["api"])


# =========================
# Models
# =========================
class SetTagBody(BaseModel):
    value: float | int | bool


# =========================
# Helpers
# =========================
def cast_value(expected_type: str, val):
    """
    Castet REST-Werte sauber auf OPC-UA / Siemens Datentypen
    """
    if expected_type in ("BOOL",):
        if isinstance(val, bool):
            return val
        if val in (0, 1):
            return bool(val)
        raise HTTPException(status_code=400, detail="Expected BOOL (true/false or 0/1)")

    if expected_type in ("REAL", "LREAL"):
        if isinstance(val, bool):
            raise HTTPException(status_code=400, detail="Expected number, got BOOL")
        return float(val)

    if expected_type in ("UInt32", "DWORD", "UDINT"):
        if isinstance(val, bool):
            raise HTTPException(status_code=400, detail="Expected integer, got BOOL")
        iv = int(val)
        if iv < 0 or iv > 0xFFFFFFFF:
            raise HTTPException(status_code=400, detail="Value out of range for UInt32")
        return iv

    if expected_type in ("INT", "DINT", "UINT"):
        if isinstance(val, bool):
            raise HTTPException(status_code=400, detail="Expected integer, got BOOL")
        return int(val)

    # fallback
    return val


# =========================
# Routes
# =========================

@router.get("/health")
async def health():
    """
    Einfacher Health-Check:
    - mindestens ein Tag 'good' => verbunden
    """
    connected = any(t["quality"] == "good" for t in CURRENT_TAGS.values())

    return {
        "status": "ok" if connected else "degraded",
        "connected": connected,
        "ts": now_ms(),
        "tag_count": len(CURRENT_TAGS),
    }


@router.get("/tags")
async def get_all_tags():
    return {
        "ts": now_ms(),
        "count": len(CURRENT_TAGS),
        "tags": list(CURRENT_TAGS.values()),
    }


@router.get("/tags/{name}")
async def get_one_tag(name: str):
    tag = CURRENT_TAGS.get(name)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not found")

    return tag


@router.post("/tags/{name}")
async def set_one_tag(name: str, body: SetTagBody):
    """
    Setzt einen Tag via REST.

    WICHTIG:
    Aktuell wird nur der lokale Cache gesetzt.
    -> Für echtes Schreiben in die S7 musst du hier OPC UA write_value() ergänzen.
    """
    if name not in TAGS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not configured")

    cfg = TAGS_CONFIG[name]
    expected_type = cfg["type"]

    # sauber casten
    value = cast_value(expected_type, body.value)

    # aktuellen Tag holen
    tag = CURRENT_TAGS.get(name)
    if not tag:
        raise HTTPException(status_code=500, detail="Tag not initialized")

    # update
    tag["value"] = value
    tag["ts_client_ms"] = now_ms()
    tag["quality"] = "set-via-rest"
    tag["status_code"] = "Good (LocalWrite)"

    return {
        "ok": True,
        "tag": tag,
    }
