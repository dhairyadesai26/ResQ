"""
ResQ Web - FastAPI Application Entrypoint
A Web-Based Process Monitoring and Automatic Recovery System for Windows
"""

import sys
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging

# Ensure workspace root is in python path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.core.config import settings
from backend.app.database.session import engine
from backend.app.database.base import Base
import backend.app.models  # Ensure models are loaded for table creation
from backend.app.api.router import api_router
from backend.app.websocket.connection_manager import ws_manager
from backend.app.services.application_service import ApplicationService
from backend.app.services.metrics_collector import metrics_collector
from agent.monitoring.monitor_engine import monitor_engine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resq.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown hooks."""
    logger.info("Initializing ResQ Web Backend...")

    # 1. Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    # 2. Attach running event loop to WebSocket connection manager
    loop = asyncio.get_running_loop()
    ws_manager.set_loop(loop)

    # 3. Synchronize persisted applications into supervisor engine
    ApplicationService.load_persisted_applications()
    logger.info("Persisted applications synchronized with process supervisor.")

    # 4. Start background metrics collector
    metrics_collector.start()

    yield

    # Shutdown sequence
    logger.info("Shutting down ResQ Web Backend...")
    metrics_collector.stop()
    monitor_engine.shutdown()
    logger.info("All supervisor engines and background threads terminated cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A Web-Based Process Monitoring and Automatic Recovery System for Windows",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "product": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "api_docs": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/system/health",
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Live WebSocket feed for application states, metrics ticks, and events."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open; receive ping or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket connection closed: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

