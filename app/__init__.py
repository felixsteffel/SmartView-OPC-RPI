import asyncio
from fastapi import FastAPI

from .api.routes import router as api_router
from .web.routes import router as web_router
from .store import init_current_tags
from .opcua_server import OpcUaServer
from .services.simulator import Simulator
from .config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="RPI OPC UA Server + REST")

    app.include_router(api_router)
    app.include_router(web_router)

    opcua_server = OpcUaServer(endpoint=settings.OPCUA_ENDPOINT)
    simulator = Simulator(interval_sec=settings.SIM_INTERVAL_SEC)

    @app.on_event("startup")
    async def _startup():
        init_current_tags()

        # Start background tasks
        app.state.tasks = []
        app.state.tasks.append(asyncio.create_task(opcua_server.run_forever()))
        if settings.ENABLE_SIMULATOR:
            app.state.tasks.append(asyncio.create_task(simulator.run_forever()))

    @app.on_event("shutdown")
    async def _shutdown():
        # Stop tasks gracefully
        await opcua_server.stop()
        await simulator.stop()

        tasks = getattr(app.state, "tasks", [])
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    return app