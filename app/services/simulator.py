# simulator.py

# Diese Klasse simuliert die Werte der Tags, bis eine echte Datenquelle vorhanden ist.
# Sie generiert periodisch neue Werte für die konfigurierten Tags und speichert sie im CURRENT_TAGS-Dictionary, damit die API und Web-Interface damit arbeiten können.

import asyncio
import random

from ..config import TAGS_CONFIG
from ..store import CURRENT_TAGS, now_ms


class Simulator:
    """
    Generates changing values into CURRENT_TAGS.
    Useful until real data source exists (sensors, Modbus, REST writes, etc).
    """

    def __init__(self, interval_sec: float = 0.5):
        self.interval_sec = interval_sec
        self._stop = asyncio.Event()
        self._toggle = False

    async def stop(self):
        self._stop.set()

    def _simulate_real(self, name: str) -> float:
        if "temp" in name:
            return round(20 + random.random() * 40, 2)
        if "pressure" in name:
            return round(1 + random.random() * 9, 2)
        return round(random.random() * 100, 2)

    def _simulate_bool(self, name: str) -> bool:
        # alternating pattern
        if "pump" in name:
            return self._toggle
        return not self._toggle

    async def run_forever(self):
        while not self._stop.is_set():
            self._toggle = not self._toggle
            ts = now_ms()

            for name, cfg in TAGS_CONFIG.items():
                if cfg["type"] == "REAL":
                    val = self._simulate_real(name)
                else:
                    val = self._simulate_bool(name)

                CURRENT_TAGS[name] = {
                    "name": name,
                    "type": cfg["type"],
                    "unit": cfg.get("unit", ""),
                    "value": val,
                    "ts": ts,
                    "quality": "simulated",
                }

            await asyncio.sleep(self.interval_sec)