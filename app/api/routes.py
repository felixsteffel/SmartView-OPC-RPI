# app/api/routes.py

# prüft den Status der Verbindung zum OPC UA Server und 
# ermöglicht das Lesen und Schreiben von Tags über HTTP-Endpoints.

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..store import CURRENT_TAGS, now_ms
from ..config import TAGS_CONFIG

router = APIRouter(prefix="/api", tags=["api"])

def require_login(request: Request):
    if request.session.get("authenticated") is not True:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")


class SetTagBody(BaseModel):
    value: float | int | bool


def is_float_display_tag(name: str) -> bool:
    cfg = TAGS_CONFIG.get(name, {})
    return cfg.get("display_type") == "FLOAT32_FROM_DWORD"


@router.get("/health")
async def health(request: Request):
    require_login(request)
    connected = any(t["quality"] in ("good", "written") for t in CURRENT_TAGS.values())
    return {
        "status": "ok" if connected else "degraded",
        "connected": connected,
        "ts": now_ms(),
        "tag_count": len(CURRENT_TAGS),
    }


@router.get("/tags")
async def get_all_tags(request: Request):
    require_login(request)
    return {
        "ts": now_ms(),
        "count": len(CURRENT_TAGS),
        "tags": list(CURRENT_TAGS.values()),
    }


@router.get("/tags/{name}")
async def get_one_tag(name: str, request: Request):
    require_login(request)
    tag = CURRENT_TAGS.get(name)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not found")
    return tag


@router.post("/tags/{name}")
async def set_one_tag(name: str, body: SetTagBody, request: Request):
    require_login(request)
    if name not in TAGS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not configured")

    cfg = TAGS_CONFIG[name]
    expected_type = cfg["type"]

    if expected_type == "BOOL":
        if isinstance(body.value, bool):
            user_value = body.value
        elif body.value in (0, 1):
            user_value = bool(body.value)
        else:
            raise HTTPException(status_code=400, detail="Expected BOOL (true/false or 0/1)")

    elif expected_type in ("REAL", "LREAL"):
        if isinstance(body.value, bool):
            raise HTTPException(status_code=400, detail="Expected number, got BOOL")
        user_value = float(body.value)

    elif expected_type in ("UInt32", "DWORD", "UDINT"):
        if isinstance(body.value, bool):
            raise HTTPException(status_code=400, detail="Expected number, got BOOL")

        if is_float_display_tag(name):
            user_value = float(body.value)
        else:
            iv = int(body.value)
            if iv < 0 or iv > 0xFFFFFFFF:
                raise HTTPException(status_code=400, detail="Value out of range for UInt32")
            user_value = iv

    elif expected_type in ("INT", "DINT", "UINT"):
        if isinstance(body.value, bool):
            raise HTTPException(status_code=400, detail="Expected integer, got BOOL")
        user_value = int(body.value)

    else:
        user_value = body.value

    reader = getattr(request.app.state, "opcua_reader", None)
    if reader is None:
        raise HTTPException(status_code=500, detail="OPC UA reader not available")

    try:
        tag = await reader.write_tag(name, user_value)
        return {"ok": True, "tag": tag}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")