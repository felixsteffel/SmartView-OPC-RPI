import asyncio
from asyncua import Client

ENDPOINT = "opc.tcp://192.168.3.12:4840"

async def main():
    async with Client(url=ENDPOINT, timeout=4) as client:
        ns = await client.get_namespace_array()
        print("Namespaces:")
        for i, x in enumerate(ns):
            print(i, x)

        objects = client.nodes.objects
        children = await objects.get_children()
        print("\nObjects children:")
        for ch in children:
            try:
                print(
                    "node=", ch,
                    "browse=", await ch.read_browse_name(),
                    "display=", await ch.read_display_name()
                )
            except Exception as e:
                print("browse err:", e)

asyncio.run(main())