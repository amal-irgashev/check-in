from fastapi import FastAPI
import logging
from core.config import get_settings
from core.middleware import setup_middleware
from api.routes import journal, chat, profile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Journal and Chat API with AI-powered analysis"
)

# Setup middleware
setup_middleware(app)

# Include routers with proper prefixes
app.include_router(journal.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)
app.include_router(profile.router, prefix=settings.API_PREFIX)

@app.get("/")
async def read_root():
    """Health check endpoint"""
    return {"message": "API is running!", "version": settings.VERSION}

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("Starting up API server...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks"""
    logger.info("Shutting down API server...")
