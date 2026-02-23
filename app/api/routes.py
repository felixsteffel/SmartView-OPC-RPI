from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from ..store import CURRENT_TAGS, now_ms
from ..config import TAGS_CONFIG

router = APIRouter(prefix="/api", tags=["api"])


class SetTagBody(BaseModel):
    value: float | bool


@router.get("/tags")
async def get_all_tags():
    return JSONResponse(content={"ts": now_ms(), "tags": list(CURRENT_TAGS.values())})


@router.get("/tags/{name}")
async def get_one_tag(name: str):
    tag = CURRENT_TAGS.get(name)
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not found")
    return JSONResponse(content=tag)


@router.post("/tags/{name}")
async def set_one_tag(name: str, body: SetTagBody):
    """
    Allows writing tag values via REST (also reflected into OPC UA variables).
    Siemens client can also write directly via OPC UA (set_writable in server).
    """
    if name not in TAGS_CONFIG:
        raise HTTPException(status_code=404, detail=f"Tag '{name}' not configured")

    expected_type = TAGS_CONFIG[name]["type"]
    val = body.value

    if expected_type == "REAL":
        if isinstance(val, bool):
            raise HTTPException(status_code=400, detail="Expected REAL (number), got BOOL")
        val = float(val)
    else:
        if not isinstance(val, bool):
            # accept 0/1 as convenience
            if val in (0, 1):
                val = bool(val)
            else:
                raise HTTPException(status_code=400, detail="Expected BOOL (true/false)")

    CURRENT_TAGS[name]["value"] = val
    CURRENT_TAGS[name]["ts"] = now_ms()
    CURRENT_TAGS[name]["quality"] = "set-via-rest"

    return {"ok": True, "tag": CURRENT_TAGS[name]}