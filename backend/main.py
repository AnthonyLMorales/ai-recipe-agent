import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cooking Assistant API",
    description="LLM-powered cooking and recipe Q&A application using LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    logger.info("Application startup complete")


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
app.include_router(router)


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
