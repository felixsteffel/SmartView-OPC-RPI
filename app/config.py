import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    OPCUA_ENDPOINT: str = os.getenv("OPCUA_ENDPOINT", "opc.tcp://192.168.3.12:4840")
    POLL_INTERVAL_SEC: float = float(os.getenv("POLL_INTERVAL_SEC", "0.5"))
    ENABLE_SIMULATOR: bool = os.getenv("ENABLE_SIMULATOR", "0") not in ("0", "false", "False")


settings = Settings()

TAGS_CONFIG = {
    "always_true": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=AlwaysTRUE",
    },
    "g1_bg1_left_sensor": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=G1-BG1",
    },
    "g1_bg2_right_sensor": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=G1-BG2",
    },
    "c1_bg2_front_position": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=C1-BG2",
    },
    "c1_bg3_rear_position": {
        "type": "BOOL",
        "unit": "",
        "nodeid": "ns=3;s=C1-BG3",
    },
}