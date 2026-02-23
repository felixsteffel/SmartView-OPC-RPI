import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # OPC UA endpoint for Siemens client to connect to
    # Example: opc.tcp://<pi-ip>:4840/rpi/
    OPCUA_ENDPOINT: str = os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0.0:4840/rpi/")

    # Optional simulator to produce values into CURRENT_TAGS
    ENABLE_SIMULATOR: bool = os.getenv("ENABLE_SIMULATOR", "1") not in ("0", "false", "False")
    SIM_INTERVAL_SEC: float = float(os.getenv("SIM_INTERVAL_SEC", "0.5"))


settings = Settings()

# Your tag model/config: keep it simple and explicit
TAGS_CONFIG = {
    "temp_c": {"type": "REAL", "unit": "°C"},
    "pressure_bar": {"type": "REAL", "unit": "bar"},
    "pump_on": {"type": "BOOL", "unit": ""},
    "valve_open": {"type": "BOOL", "unit": ""},
}