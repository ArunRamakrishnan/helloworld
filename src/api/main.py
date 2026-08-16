"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

DISCLAIMER = get_config().disclaimer


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    logger.info("Indian Investment Research Wizard starting up")  # pragma: no cover
    yield  # pragma: no cover
    logger.info("Shutting down")  # pragma: no cover


app = FastAPI(
    title="Indian Investment Research Wizard",
    description=(
        "AI-powered investment research for NSE/BSE equities. "
        f"{DISCLAIMER}"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "disclaimer": DISCLAIMER}
