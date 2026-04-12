# opcua_client.py

# Verwaltung der OPC UA Verbindung, Lesen der Tag-Werte und Schreiben von Werten auf die SPS.
# Die Klasse OpcUaReader kümmert sich um die Verbindung, das periodische Lesen der Werte

import asyncio
import struct
from datetime import datetime
from typing import Any, Optional

from asyncua import ua
from .config import settings, TAGS_CONFIG
from .store import CURRENT_TAGS, now_ms

try:
    from asyncua import Client as OPCUAClient
except Exception:
    OPCUAClient = None


def iso_or_none(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def uint32_to_float32(value: int) -> float:
    return struct.unpack(">f", struct.pack(">I", value))[0]


def float32_to_uint32(value: float) -> int:
    return struct.unpack(">I", struct.pack(">f", float(value)))[0]


def apply_read_transform(value, cfg):
    if value is None:
        return None

    if cfg.get("display_type") == "FLOAT32_FROM_DWORD":
        return uint32_to_float32(int(value))

    return value


def apply_write_transform(value, cfg):
    """
    Wert aus REST/UI -> tatsächlicher SPS/OPC-UA Schreibwert
    """
    if value is None:
        return None

    if cfg.get("display_type") == "FLOAT32_FROM_DWORD":
        return float32_to_uint32(float(value))

    return value


class OpcUaReader:
    def __init__(self, endpoint: str, poll_interval: float):
        self.endpoint = endpoint
        self.poll_interval = poll_interval
        self._stop = asyncio.Event()
        self._connected = False
        self._client: Optional[Any] = None
        self._nodes: dict[str, Any] = {}
        self._lock = asyncio.Lock()

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
                raw_value = dv.Value.Value if dv.Value is not None else None
                value = apply_read_transform(raw_value, cfg)

                status_code = str(dv.StatusCode) if dv.StatusCode is not None else None
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
                    "raw_value": raw_value,
                    "ts_client_ms": now_ms(),
                    "ts_source": iso_or_none(getattr(dv, "SourceTimestamp", None)),
                    "ts_server": iso_or_none(getattr(dv, "ServerTimestamp", None)),
                    "quality": quality,
                    "status_code": status_code,
                }

            except Exception as e:
                CURRENT_TAGS[name]["value"] = None
                CURRENT_TAGS[name]["quality"] = "read-error"
                CURRENT_TAGS[name]["status_code"] = f"{type(e).__name__}: {e}"
                CURRENT_TAGS[name]["ts_client_ms"] = now_ms()
                print(f"[OPCUA READ ERROR] tag={name} nodeid={cfg['nodeid']} err={type(e).__name__}: {e}")

    async def write_tag(self, name: str, value: Any):
        """
        Schreibt einen Tag wirklich auf die SPS via OPC UA.
        value ist der UI/REST-Wert.
        """
        if name not in TAGS_CONFIG:
            raise KeyError(f"Tag '{name}' not configured")

        if not self._connected or self._client is None:
            raise RuntimeError("OPC UA client is not connected")

        cfg = TAGS_CONFIG[name]
        node = self._nodes.get(name)
        if node is None:
            raise RuntimeError(f"Node for tag '{name}' is not available")

        plc_value = apply_write_transform(value, cfg)
        if plc_value is None:
            raise ValueError("Write value must not be None")

        expected_type = cfg["type"]

        # passenden OPC-UA VariantType wählen
        if expected_type == "BOOL":
            variant = ua.Variant(bool(plc_value), ua.VariantType.Boolean)

        elif expected_type in ("UInt32", "DWORD", "UDINT"):
            iv = int(plc_value)
            if iv < 0 or iv > 0xFFFFFFFF:
                raise ValueError("Value out of range for UInt32")
            variant = ua.Variant(iv, ua.VariantType.UInt32)

        elif expected_type in ("REAL",):
            variant = ua.Variant(float(plc_value), ua.VariantType.Float)

        elif expected_type in ("LREAL",):
            variant = ua.Variant(float(plc_value), ua.VariantType.Double)

        elif expected_type in ("INT",):
            variant = ua.Variant(int(plc_value), ua.VariantType.Int16)

        elif expected_type in ("DINT",):
            variant = ua.Variant(int(plc_value), ua.VariantType.Int32)

        elif expected_type in ("UINT",):
            variant = ua.Variant(int(plc_value), ua.VariantType.UInt16)

        else:
            raise ValueError(f"Unsupported write type: {expected_type}")

        async with self._lock:
            await node.write_value(variant)

            # danach direkt frisch lesen, damit UI exakt den SPS-Zustand sieht
            dv = await node.read_data_value()
            raw_value = dv.Value.Value if dv.Value is not None else None
            display_value = apply_read_transform(raw_value, cfg)

            CURRENT_TAGS[name] = {
                "name": name,
                "plc_name": cfg.get("plc_name", name),
                "nodeid": cfg["nodeid"],
                "type": cfg["type"],
                "unit": cfg.get("unit", ""),
                "description": cfg.get("description", ""),
                "value": display_value,
                "raw_value": raw_value,
                "ts_client_ms": now_ms(),
                "ts_source": iso_or_none(getattr(dv, "SourceTimestamp", None)),
                "ts_server": iso_or_none(getattr(dv, "ServerTimestamp", None)),
                "quality": "written",
                "status_code": str(dv.StatusCode) if dv.StatusCode is not None else "Good",
            }

            return CURRENT_TAGS[name]

    async def run_forever(self):
        backoff = 1.0

        while not self._stop.is_set():
            if not self._connected:
                try:
                    await self._connect()
                    backoff = 1.0
                except Exception as e:
                    await self._mark_all("connect-failed")
                    print(f"[OPCUA CONNECT ERROR] endpoint={self.endpoint} err={type(e).__name__}: {e}")
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