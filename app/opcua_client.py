import asyncio
from typing import Any, Optional

from .config import settings, TAGS_CONFIG
from .store import CURRENT_TAGS, now_ms

try:
    from asyncua import Client as OPCUAClient
except Exception:
    OPCUAClient = None


class OpcUaReader:
    def __init__(self, endpoint: str = settings.OPCUA_ENDPOINT, poll_interval: float = settings.POLL_INTERVAL_SEC):
        self.endpoint = endpoint
        self.poll_interval = poll_interval
        self._stop = asyncio.Event()
        self._connected = False
        self._client: Optional[Any] = None

    async def stop(self):
        self._stop.set()
        await self._disconnect()

    async def _connect(self):
        if OPCUAClient is None:
            raise RuntimeError("asyncua nicht verfügbar. Installiere: uv add asyncua")

        self._client = OPCUAClient(url=self.endpoint, timeout=4)
        await self._client.connect()
        self._connected = True

    async def _disconnect(self):
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._connected = False

    async def _read_poll(self) -> None:
        if not self._connected or self._client is None:
            for name in CURRENT_TAGS:
                CURRENT_TAGS[name]["quality"] = "disconnected"
                CURRENT_TAGS[name]["ts"] = now_ms()
            return

        for name, cfg in TAGS_CONFIG.items():
            nodeid = cfg.get("nodeid")
            if not nodeid:
                CURRENT_TAGS[name]["quality"] = "no-nodeid"
                CURRENT_TAGS[name]["ts"] = now_ms()
                continue

            try:
                node = self._client.get_node(nodeid)
                val = await node.read_value()

                CURRENT_TAGS[name] = {
                    "name": name,
                    "type": cfg["type"],
                    "unit": cfg.get("unit", ""),
                    "value": val,
                    "ts": now_ms(),
                    "quality": "good",
                }
            except Exception:
                CURRENT_TAGS[name]["quality"] = "read-error"
                CURRENT_TAGS[name]["ts"] = now_ms()

    async def run_forever(self):
        backoff = 1.0

        while not self._stop.is_set():
            if not self._connected:
                try:
                    await self._connect()
                    backoff = 1.0
                except Exception:
                    for name in CURRENT_TAGS:
                        CURRENT_TAGS[name]["quality"] = "connect-failed"
                        CURRENT_TAGS[name]["ts"] = now_ms()
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