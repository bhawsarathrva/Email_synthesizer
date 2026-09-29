import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path for direct python execution
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import settings
from backend.app.database.connection import test_connection
from backend.app.api.emails import router as emails_router
from backend.app.api.verification import router as verification_router
from backend.app.api.statistics import router as statistics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("email_agent.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Test DB connection and report
    logger.info("Initializing Email Classification Agent application...")
    db_status = test_connection()
    if db_status.get("status") == "connected":
        logger.info(f"Connected to NeonDB: Database={db_status.get('database')} | User={db_status.get('user')}")
    else:
        logger.warning(f"NeonDB connection warning: {db_status.get('error')}")
    yield
    logger.info("Shutting down Email Classification Agent application.")


app = FastAPI(
    title="AI Email Classification Agent",
    description="Agentic email classification with Neon PostgreSQL and Human-in-the-Loop verification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(emails_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")

# Also include root-level /emails, /statistics, /evaluation for direct compliance with spec
app.include_router(emails_router)
app.include_router(verification_router)
app.include_router(statistics_router)


@app.get("/health")
def health_check():
    """Health check endpoint validating API and NeonDB connectivity."""
    db_status = test_connection()
    return {
        "status": "ok" if db_status.get("status") == "connected" else "degraded",
        "llm_provider": settings.LLM_PROVIDER,
        "model_name": settings.MODEL_NAME,
        "database": db_status
    }


# Frontend static files mounting
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.exists(frontend_dist):
    app.mount("/static", StaticFiles(directory=frontend_dist), name="static")

    @app.get("/")
    def serve_index():
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Email Classification Agent API is running. Browse /docs for interactive Swagger API documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
