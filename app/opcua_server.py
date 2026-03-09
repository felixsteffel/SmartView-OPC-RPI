import asyncio
from typing import Dict, Optional

from asyncua import Server, ua

from .config import TAGS_CONFIG
from .store import CURRENT_TAGS

from typing import Dict, Optional, Any


class OpcUaServer:
    """
    Exposes TAGS_CONFIG as OPC UA variables under:
      Objects -> RPI -> <tagname>

    Default endpoint example:
      opc.tcp://0.0.0.0:4840/rpi/
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._stop = asyncio.Event()
        self._server: Optional[Server] = None
        self._nodes: Dict[str, Any] = {}
        self._ns_idx: Optional[int] = None

    async def stop(self):
        self._stop.set()
        if self._server is not None:
            try:
                await self._server.stop()
            except Exception:
                pass
        self._server = None
        self._nodes = {}
        self._ns_idx = None

    async def _start_server(self):
        server = Server()
        await server.init()
        server.set_endpoint(self.endpoint)
        server.set_server_name("RPI OPC UA Server")

        # Namespace
        uri = "urn:rpi:opcua"
        ns_idx = await server.register_namespace(uri)

        # Root object for our tags
        objects = server.nodes.objects
        rpi_obj = await objects.add_object(ns_idx, "RPI")

        # Create variables
        nodes: Dict[str, Any] = {}
        for name, cfg in TAGS_CONFIG.items():
            vtype = ua.VariantType.Double if cfg["type"] == "REAL" else ua.VariantType.Boolean
            initial = 0.0 if cfg["type"] == "REAL" else False

            var = await rpi_obj.add_variable(ns_idx, name, ua.Variant(initial, vtype))

            # Allow Siemens client to write too (optional but handy)
            await var.set_writable()

            nodes[name] = var

        self._server = server
        self._nodes = nodes
        self._ns_idx = ns_idx

        await server.start()

    async def _sync_loop(self):
        # Push CURRENT_TAGS values into OPC UA nodes periodically
        while not self._stop.is_set():
            try:
                for name, node in self._nodes.items():
                    tag = CURRENT_TAGS.get(name)
                    if not tag:
                        continue
                    await node.write_value(tag["value"])
            except Exception:
                # keep server alive even if one update fails
                pass
            await asyncio.sleep(0.2)

    async def run_forever(self):
        """
        Start OPC UA server and run until stopped.
        """
        await self._start_server()
        await self._sync_loop()