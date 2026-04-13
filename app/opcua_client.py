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


def apply_read_transform(value: Any, cfg: dict[str, Any]) -> Any:
    if value is None:
        return None

    if cfg.get("display_type") == "FLOAT32_FROM_DWORD":
        return uint32_to_float32(int(value))

    return value


def apply_write_transform(value: Any, cfg: dict[str, Any]) -> int | float | bool:
    if value is None:
        raise ValueError("Write value must not be None")

    if cfg.get("display_type") == "FLOAT32_FROM_DWORD":
        return float32_to_uint32(float(value))

    return value


class TagSubscriptionHandler:
    def __init__(self, reader: "OpcUaReader"):
        self.reader = reader

    async def datachange_notification(self, node, val, data):
        await self.reader.handle_datachange(node=node, val=val, data=data)

    async def status_change_notification(self, status):
        print(f"[OPCUA STATUS CHANGE] {status}")


class OpcUaReader:
    def __init__(self, endpoint: str, publish_interval_ms: int = 500):
        self.endpoint = endpoint
        self.publish_interval_ms = publish_interval_ms
        self._stop = asyncio.Event()
        self._connected = False
        self._client: Optional[Any] = None
        self._nodes: dict[str, Any] = {}
        self._nodeid_to_name: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._subscription: Optional[Any] = None
        self._subscription_handler = TagSubscriptionHandler(self)

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
        self._nodeid_to_name = {
            str(node.nodeid): name
            for name, node in self._nodes.items()
        }
        self._connected = True

    async def _create_subscription(self):
        if self._client is None:
            raise RuntimeError("Client not connected")

        self._subscription = await self._client.create_subscription(
            self.publish_interval_ms,
            self._subscription_handler,
        )

        for name, node in self._nodes.items():
            await self._subscription.subscribe_data_change(node)

            # optionaler Initial-Read, damit direkt beim Start Werte da sind
            try:
                dv = await node.read_data_value()
                raw_value = dv.Value.Value if dv.Value is not None else None
                await self._update_tag_from_datavalue(name=name, cfg=TAGS_CONFIG[name], dv=dv, raw_value=raw_value)
            except Exception as e:
                CURRENT_TAGS[name]["value"] = None
                CURRENT_TAGS[name]["quality"] = "read-error"
                CURRENT_TAGS[name]["status_code"] = f"{type(e).__name__}: {e}"
                CURRENT_TAGS[name]["ts_client_ms"] = now_ms()
                print(f"[OPCUA INITIAL READ ERROR] tag={name} nodeid={TAGS_CONFIG[name]['nodeid']} err={type(e).__name__}: {e}")

    async def _disconnect(self):
        if self._subscription is not None:
            try:
                await self._subscription.delete()
            except Exception:
                pass

        self._subscription = None

        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass

        self._client = None
        self._nodes = {}
        self._nodeid_to_name = {}
        self._connected = False

    async def _mark_all(self, quality: str):
        ts = now_ms()
        for name in CURRENT_TAGS:
            CURRENT_TAGS[name]["quality"] = quality
            CURRENT_TAGS[name]["ts_client_ms"] = ts

    async def _update_tag_from_datavalue(self, name: str, cfg: dict[str, Any], dv: Any, raw_value: Any):
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

    async def handle_datachange(self, node: Any, val: Any, data: Any):
        try:
            nodeid_str = str(node.nodeid)
            name = self._nodeid_to_name.get(nodeid_str)

            if name is None:
                print(f"[OPCUA DATACHANGE WARNING] Unknown node: {nodeid_str}")
                return

            cfg = TAGS_CONFIG[name]

            # data.monitored_item.Value enthält normalerweise das komplette DataValue
            dv = None
            raw_value = val

            if hasattr(data, "monitored_item") and hasattr(data.monitored_item, "Value"):
                dv = data.monitored_item.Value
                raw_value = dv.Value.Value if dv.Value is not None else val

            if dv is None:
                # Fallback, falls asyncua in einer anderen Form liefert
                CURRENT_TAGS[name] = {
                    "name": name,
                    "plc_name": cfg.get("plc_name", name),
                    "nodeid": cfg["nodeid"],
                    "type": cfg["type"],
                    "unit": cfg.get("unit", ""),
                    "description": cfg.get("description", ""),
                    "value": apply_read_transform(raw_value, cfg),
                    "raw_value": raw_value,
                    "ts_client_ms": now_ms(),
                    "ts_source": None,
                    "ts_server": None,
                    "quality": "good",
                    "status_code": "Good",
                }
                return

            await self._update_tag_from_datavalue(name=name, cfg=cfg, dv=dv, raw_value=raw_value)

        except Exception as e:
            print(f"[OPCUA DATACHANGE ERROR] err={type(e).__name__}: {e}")

    async def write_tag(self, name: str, value: Any):
        if name not in TAGS_CONFIG:
            raise KeyError(f"Tag '{name}' not configured")

        if not self._connected or self._client is None:
            raise RuntimeError("OPC UA client is not connected")

        cfg = TAGS_CONFIG[name]
        node = self._nodes.get(name)
        if node is None:
            raise RuntimeError(f"Node for tag '{name}' is not available")

        plc_value = apply_write_transform(value, cfg)
        expected_type = cfg["type"]

        if expected_type == "BOOL":
            variant = ua.Variant(bool(plc_value), ua.VariantType.Boolean)

        elif expected_type in ("UInt32", "DWORD", "UDINT"):
            iv = int(plc_value)
            if iv < 0 or iv > 0xFFFFFFFF:
                raise ValueError("Value out of range for UInt32")
            variant = ua.Variant(iv, ua.VariantType.UInt32)

        elif expected_type == "REAL":
            variant = ua.Variant(float(plc_value), ua.VariantType.Float)

        elif expected_type == "LREAL":
            variant = ua.Variant(float(plc_value), ua.VariantType.Double)

        elif expected_type == "INT":
            variant = ua.Variant(int(plc_value), ua.VariantType.Int16)

        elif expected_type == "DINT":
            variant = ua.Variant(int(plc_value), ua.VariantType.Int32)

        elif expected_type == "UINT":
            variant = ua.Variant(int(plc_value), ua.VariantType.UInt16)

        else:
            raise ValueError(f"Unsupported write type: {expected_type}")

        async with self._lock:
            await node.write_value(variant)

            # optional direkt lesen; meist kommt kurz danach ohnehin die Subscription-Meldung
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
                    await self._create_subscription()
                    backoff = 1.0
                except Exception as e:
                    await self._mark_all("connect-failed")
                    print(f"[OPCUA CONNECT/SUBSCRIBE ERROR] endpoint={self.endpoint} err={type(e).__name__}: {e}")
                    await self._disconnect()
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 15.0)
                    continue

            try:
                # keine Poll-Schleife mehr; Verbindung am Leben halten
                await asyncio.wait_for(self._stop.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            except Exception:
                await self._disconnect()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 15.0)