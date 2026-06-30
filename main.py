from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router


# Logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_db()
    yield
    logger.info("Shutting down...")
    await close_db()
    
    
# creating the app instance 

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Commission tracking SaaS for sales organizations",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)
register_exception_handlers(app)


# Middlewaree

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    TrustedHostMiddleware,
)


# routes
app.include_router(api_router, prefix="/api/v1")


#Health Checking
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "v1"}


os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="uploads"), name="static")
