# store.py
import time
from typing import Any, Dict
from .config import TAGS_CONFIG

def now_ms() -> int:
    return int(time.time() * 1000)

CURRENT_TAGS: Dict[str, Dict[str, Any]] = {}

def default_value_for(tag_type: str):
    if tag_type in ("BOOL",):
        return False
    if tag_type in ("UInt32", "DWORD", "UDINT", "UINT", "INT", "DINT", "REAL", "LREAL"):
        return 0
    return None

def init_current_tags() -> None:
    CURRENT_TAGS.clear()
    for name, cfg in TAGS_CONFIG.items():
        CURRENT_TAGS[name] = {
            "name": name,
            "plc_name": cfg.get("plc_name", name),
            "nodeid": cfg["nodeid"],
            "type": cfg["type"],
            "unit": cfg.get("unit", ""),
            "description": cfg.get("description", ""),
            "value": default_value_for(cfg["type"]),
            "ts_client_ms": now_ms(),
            "ts_source": None,
            "ts_server": None,
            "quality": "init",
            "status_code": None,
        }