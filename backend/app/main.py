from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.views.router import router as views_router
# 👇 AGREGA ESTA IMPORTACIÓN AQUÍ
from app.modules.stations.router import router as stations_router
from app.core.config import settings
from app.core.logger import logger
from app.modules.tables.model import Table


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("===================================")
    logger.info("Criptonix Restaurant iniciado")
    logger.info("===================================")

    yield

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
