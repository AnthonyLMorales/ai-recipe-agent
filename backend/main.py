import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import conversations_router, cooking_router
from database.init import create_tables

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    create_tables()
    logger.info("Application startup complete")
    yield
    # Shutdown (if needed in the future)
    logger.info("Application shutdown")


app = FastAPI(
    title="Cooking Assistant API",
    description="LLM-powered cooking and recipe Q&A application using LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "http://frontend:3000",  # Docker network
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(cooking_router)
app.include_router(conversations_router)


@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: API name and status
    """
    return {"message": "Cooking Assistant API", "status": "running"}


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancer probes.

    Returns:
        dict: Health status indicator
    """
    return {"status": "healthy"}
