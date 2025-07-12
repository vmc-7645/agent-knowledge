import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routes import router as semantic_router

# Optional: If db.py exposes engine / Base, create tables on startup
try:
    from .db import engine, Base  # type: ignore
except ImportError:  # pragma: no cover
    engine = None  # noqa: PGH003 – fallback when Base/engine aren't available
    Base = None

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------

load_dotenv()

API_TITLE = os.getenv("API_TITLE", "Agent-Knowledge API")
API_VERSION = os.getenv("API_VERSION", "0.1.0")

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(title=API_TITLE, version=API_VERSION)

# CORS configuration (ENV: CORS_ORIGINS="http://localhost:3000,https://myapp.com")
origins_raw = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include semantic QA routes
app.include_router(semantic_router)


# -----------------------------------------------------------------------------
# Startup / shutdown hooks
# -----------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Create tables if the ORM Base is available and engine is imported."""
    if engine is not None and Base is not None:
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:  # pragma: no cover
            # Don't crash the app if migrations are handled elsewhere
            print(f"[startup-warning] Failed to create tables automatically: {exc}")


@app.get("/", tags=["health"])
async def root():
    """Healthcheck endpoint."""
    return {"status": "ok"}


# -----------------------------------------------------------------------------
# Application entrypoint (for `python -m server.main`)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)
