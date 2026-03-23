# opcua_client.py
import asyncio
from datetime import datetime
from typing import Any, Optional

from .config import settings, TAGS_CONFIG
from .store import CURRENT_TAGS, now_ms

try:
    from asyncua import Client as OPCUAClient
except Exception:
    OPCUAClient = None


def iso_or_none(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


class OpcUaReader:
    def __init__(self, endpoint: str, poll_interval: float):
        self.endpoint = endpoint
        self.poll_interval = poll_interval
        self._stop = asyncio.Event()
        self._connected = False
        self._client: Optional[Any] = None
        self._nodes: dict[str, Any] = {}

    async def stop(self):
        self._stop.set()
        await self._disconnect()

    async def _connect(self):
        if OPCUAClient is None:
            raise RuntimeError("asyncua nicht verfügbar. Installiere z. B. mit: pip install asyncua")

        client = OPCUAClient(url=self.endpoint, timeout=4)

        if settings.OPCUA_USERNAME:
            client.set_user(settings.OPCUA_USERNAME)
            client.set_password(settings.OPCUA_PASSWORD)

        await client.connect()

        self._client = client
        self._nodes = {
            name: client.get_node(cfg["nodeid"])
            for name, cfg in TAGS_CONFIG.items()
        }
        self._connected = True

    async def _disconnect(self):
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._nodes = {}
        self._connected = False

    async def _mark_all(self, quality: str):
        ts = now_ms()
        for name in CURRENT_TAGS:
            CURRENT_TAGS[name]["quality"] = quality
            CURRENT_TAGS[name]["ts_client_ms"] = ts

    async def _read_poll(self) -> None:
        if not self._connected or self._client is None:
            await self._mark_all("disconnected")
            return

        for name, cfg in TAGS_CONFIG.items():
            try:
                dv = await self._nodes[name].read_data_value()
                value = dv.Value.Value if dv.Value is not None else None
                status_code = str(dv.StatusCode) if dv.StatusCode is not None else None

                # guter Default: alles, was nicht Bad ist, als good behandeln
                quality = "good"
                if status_code and "Bad" in status_code:
                    quality = "bad"

                CURRENT_TAGS[name] = {
                    "name": name,
                    "plc_name": cfg.get("plc_name", name),
                    "nodeid": cfg["nodeid"],
                    "type": cfg["type"],
                    "unit": cfg.get("unit", ""),
                    "description": cfg.get("description", ""),
                    "value": value,
                    "ts_client_ms": now_ms(),
                    "ts_source": iso_or_none(getattr(dv, "SourceTimestamp", None)),
                    "ts_server": iso_or_none(getattr(dv, "ServerTimestamp", None)),
                    "quality": quality,
                    "status_code": status_code,
                }
            except Exception as e:
                CURRENT_TAGS[name]["quality"] = "read-error"
                CURRENT_TAGS[name]["status_code"] = type(e).__name__
                CURRENT_TAGS[name]["ts_client_ms"] = now_ms()

    async def run_forever(self):
        backoff = 1.0

        while not self._stop.is_set():
            if not self._connected:
                try:
                    await self._connect()
                    backoff = 1.0
                except Exception:
                    await self._mark_all("connect-failed")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 15.0)
                    continue

            try:
                await self._read_poll()
                await asyncio.sleep(self.poll_interval)
            except Exception:
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15.0)