import asyncio
from fastapi import FastAPI

from .api.routes import router as api_router
from .web.routes import router as web_router
from .store import init_current_tags
from .opcua_client import OpcUaReader
from .config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="RPI OPC UA Client + REST")

    app.include_router(api_router)
    app.include_router(web_router)

    reader = OpcUaReader(
        endpoint=settings.OPCUA_ENDPOINT,
        poll_interval=settings.POLL_INTERVAL_SEC,
    )

    @app.on_event("startup")
    async def _startup():
        init_current_tags()
        app.state.tasks = [asyncio.create_task(reader.run_forever())]

    @app.on_event("shutdown")
    async def _shutdown():
        await reader.stop()

        tasks = getattr(app.state, "tasks", [])
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    return app