# app/__init__.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api.routes import router as api_router
from .web.routes import router as web_router
from .store import init_current_tags
from .opcua_client import OpcUaReader
from .config import settings


def create_app() -> FastAPI:
    reader = OpcUaReader(
        endpoint=settings.OPCUA_ENDPOINT,
        poll_interval=settings.POLL_INTERVAL_SEC,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_current_tags()
        task = asyncio.create_task(reader.run_forever())
        app.state.tasks = [task]
        try:
            yield
        finally:
            await reader.stop()
            for t in app.state.tasks:
                t.cancel()
            await asyncio.gather(*app.state.tasks, return_exceptions=True)

    app = FastAPI(
        title="RPI OPC UA Client + REST + Web",
        lifespan=lifespan,
    )

    app.include_router(api_router)
    app.include_router(web_router)
    return app