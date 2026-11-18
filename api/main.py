import base64
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from api.routes import router as api_router
from config.settings import settings
from db.database import Base, SessionLocal, engine, get_db
from db.seed import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.auto_seed_demo:
        with SessionLocal() as db:
            seed_initial_data(db)
    yield


app = FastAPI(
    title="Sovereign Multi-Modal Trade Opportunity Intelligence Platform",
    description="Powered by Gemini 4 Carbon (thinking_level controls) with satellite & multi-modal fact-checking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def basic_auth_gate(request: Request, call_next):
    """If DASHBOARD_PASSWORD is set, require HTTP Basic auth everywhere except the health check."""
    if not settings.dashboard_password or request.url.path == "/healthz":
        return await call_next(request)

    header = request.headers.get("authorization", "")
    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8")
            _, _, password = decoded.partition(":")
            if secrets.compare_digest(password.encode(), settings.dashboard_password.encode()):
                return await call_next(request)
        except Exception:
            pass
    return Response(
        status_code=401,
        content="Authentication required",
        headers={"WWW-Authenticate": 'Basic realm="Trade Intelligence"'},
    )


app.include_router(api_router)


@app.get("/healthz", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Render zero-downtime deployment health check verifying database connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "model": settings.gemini_model}


dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
app.mount("/static", StaticFiles(directory=str(dashboard_dir)), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    return FileResponse(str(dashboard_dir / "index.html"))
