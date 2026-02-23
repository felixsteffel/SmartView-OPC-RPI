import time
from typing import Any, Dict

from .config import TAGS_CONFIG


def now_ms() -> int:
    return int(time.time() * 1000)


# shared state: latest tag values
CURRENT_TAGS: Dict[str, Dict[str, Any]] = {}


def init_current_tags() -> None:
    for name, cfg in TAGS_CONFIG.items():
        CURRENT_TAGS[name] = {
            "name": name,
            "type": cfg["type"],
            "unit": cfg.get("unit", ""),
            "value": 0.0 if cfg["type"] == "REAL" else False,
            "ts": now_ms(),
            "quality": "init",
        }