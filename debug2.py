# debug2.py
# Dieses Skript verbindet sich mit dem OPC UA Server, durchsucht die Knoten und versucht, die NodeIDs der angegebenen Ziel-Tags zu finden.

import asyncio
from asyncua import Client

ENDPOINT = "opc.tcp://192.168.3.12:4840"

TARGETS = ["AlwaysTRUE", "G1-BG1", "G1-BG2", "C1-BG1", "C1-BG2", "AnalogDruckOut"]

async def search_recursive(node, targets, found, depth=0, max_depth=10):
    if depth > max_depth:
        return

    try:
        bn = await node.read_browse_name()
        dn = await node.read_display_name()
        nodeid = node.nodeid.to_string()

        for t in targets:
            if bn.Name == t or dn.Text == t:
                found[t] = nodeid
                print(f"FOUND {t}: {nodeid}")

        for child in await node.get_children():
            await search_recursive(child, targets, found, depth + 1, max_depth)

    except Exception:
        pass

async def main():
    found = {}

    async with Client(url=ENDPOINT, timeout=4) as client:
        plc = client.get_node("ns=3;s=PLC")
        await search_recursive(plc, TARGETS, found)

    print("\\nERGEBNIS:")
    for t in TARGETS:
        print(t, "->", found.get(t, "NICHT GEFUNDEN"))

asyncio.run(main())