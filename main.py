from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging


# Logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    # await init_db()
    yield
    logger.info("Shutting down...")
    # await close_db()
    
    
# creating the app instance 

app = FastAPI()


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
app.include_router(prefix="/api/v1")


#Health Checking
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "v1"}