import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    OPCUA_ENDPOINT: str = os.getenv("OPCUA_ENDPOINT", "opc.tcp://192.168.3.10:4840")
    POLL_INTERVAL_SEC: float = float(os.getenv("POLL_INTERVAL_SEC", "0.5"))
    ENABLE_SIMULATOR: bool = os.getenv("ENABLE_SIMULATOR", "0") not in ("0", "false", "False")


settings = Settings()

TAGS_CONFIG = {
    "temp_c": {
        "type": "REAL",
        "unit": "°C",
        "nodeid": "ns=3;s=temp_c",
    },
    "pressure_bar": {
        "type": "REAL",
        "unit": "bar",
        "nodeid": "ns=3;s=pressure_bar",
    },
    "pump_on": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=pump_on",
    },
    "valve_open": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=valve_open",
    },
}