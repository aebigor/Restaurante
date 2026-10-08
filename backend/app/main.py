from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.views.router import router as views_router
# 👇 AGREGA ESTA IMPORTACIÓN AQUÍ
from app.modules.stations.router import router as stations_router
from app.core.config import settings
from app.core.logger import logger
from app.modules.tables.model import Table


async def _push_scanner_loop():
    from app.modules.push.scanner import scan
    while True:
        try: await asyncio.to_thread(scan)
        except asyncio.CancelledError: raise
        except Exception as exc: logger.warning(f"Web Push scanner: {exc}")
        await asyncio.sleep(15)


async def lifespan(app: FastAPI):

    logger.info("===================================")
    logger.info("Criptonix Restaurant iniciado")
    push_task = asyncio.create_task(_push_scanner_loop())
    logger.info("===================================")

    yield

    push_task.cancel()
    try: await push_task
    except asyncio.CancelledError: pass
    logger.info("===================================")
    logger.info("Servidor detenido")
    logger.info("===================================")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Archivos estáticos
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# Vistas HTML
app.include_router(views_router)

# API Centralizada
app.include_router(api_router)

# API de Estaciones individual
app.include_router(
    stations_router,
    prefix="/api"
)
