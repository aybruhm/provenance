from contextlib import asynccontextmanager

from fastapi import FastAPI

from dbs.postgres.engine import cleanup_connections, test_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await test_connection()
    yield
    await cleanup_connections()


app = FastAPI(
    title="Sentinel API",
    description="API for Sentinel, the compliance and governance middleware for AI agent deployments.",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api",
)


@app.get("/health")
async def health_check():
    """Health check endpoint to verify that the API is running."""
    return {"status": "ok"}
