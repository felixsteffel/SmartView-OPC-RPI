# config.py

# Hier werden die Einstellungen für die OPC UA Verbindung und die Tag-Konfiguration definiert.
# Die Tags werden mit Eigenschaften konfiguriert, die den Zugriff und die Interpretation der Werte erleichtern.

import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    OPCUA_ENDPOINT: str = os.getenv("OPCUA_ENDPOINT", "opc.tcp://192.168.3.12:4840")
    POLL_INTERVAL_SEC: float = float(os.getenv("POLL_INTERVAL_SEC", "0.5"))
    OPCUA_USERNAME: str = os.getenv("OPCUA_USERNAME", "")
    OPCUA_PASSWORD: str = os.getenv("OPCUA_PASSWORD", "")
    ENABLE_SIMULATOR: bool = os.getenv("ENABLE_SIMULATOR", "0").lower() not in ("0", "false")

settings = Settings()

TAGS_CONFIG = {
    "always_true": {
        "plc_name": "AlwaysTRUE",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="AlwaysTRUE"',
    },
    "g1_bg1_left_sensor": {
        "plc_name": "G1-BG1",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="G1-BG1"',
        "description": "optischer Sensor Links (NC)",
    },
    "g1_bg2_right_sensor": {
        "plc_name": "G1-BG2",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="G1-BG2"',
        "description": "optischer Sensor Rechts (NC)",
    },
    "c1_bg1_rear_position": {
        "plc_name": "C1-BG1",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="C1-BG1"',
        "description": "Zylinder hintere Endlage (NO)",
    },
    "c1_bg2_front_position": {
        "plc_name": "C1-BG2",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="C1-BG2"',
        "description": "Zylinder vordere Endlage (NO)",
    },
    "analog_druck_out": {
        "plc_name": "AnalogDruckOut",
        "type": "UInt32",
        "display_type": "FLOAT32_FROM_DWORD",
        "unit": "bar",
        "nodeid": 'ns=3;s="AnalogDruckOut"',
    },
    "Zylinder ausfahren": {
        "plc_name": "C1-MB1",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="C1-MB1"',
    },
    "Zylinder einfahren": {
        "plc_name": "C1-MB2",
        "type": "BOOL",
        "unit": "",
        "nodeid": 'ns=3;s="C1-MB2"',
    },



}