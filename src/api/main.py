from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from src.api.routers import (
    agent_config,
    config,
    dashboard,
    notebook,
    profile,
    settings,
    system,
)
from src.api.utils.auth import extract_bearer_token, validate_access_token
from src.logging import get_logger
from src.services.auth import engine, get_auth_routers
from src.services.auth.config import validate_auth_settings

logger = get_logger("API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")

    validate_auth_settings()

    try:
        from src.services.llm import get_llm_client

        llm_client = get_llm_client()
        logger.info(f"LLM client initialized: model={llm_client.config.model}")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM client at startup: {e}")

    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="EducAgent API",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

PROTECTED_API_PREFIX = "/api/v1"
AUTH_ROUTE_PREFIX = "/auth"


def _sanitize_request_body_for_logs(body: bytes) -> str:
    if not body:
        return "<empty>"

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return "<non-json body>"

    if isinstance(payload, dict):
        sanitized = {
            key: ("<redacted>" if "password" in key.lower() else value)
            for key, value in payload.items()
        }
        return json.dumps(sanitized, ensure_ascii=True, sort_keys=True)

    return json.dumps(payload, ensure_ascii=True)


def _unauthorized_response(*, invalid_token: bool = False) -> JSONResponse:
    www_authenticate = "Bearer"
    if invalid_token:
        www_authenticate += ' error="invalid_token"'

    return JSONResponse(
        status_code=401,
        content={"detail": "Unauthorized"},
        headers={"WWW-Authenticate": www_authenticate},
    )


@app.middleware("http")
async def auth_guard_middleware(request: Request, call_next):
    path = request.url.path

    if request.method == "OPTIONS":
        return await call_next(request)

    if not path.startswith(PROTECTED_API_PREFIX):
        return await call_next(request)

    token = extract_bearer_token(request.headers.get("Authorization"))
    if not token:
        return _unauthorized_response()

    try:
        validate_access_token(token)
    except ValueError:
        return _unauthorized_response(invalid_token=True)

    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def log_request_validation_error(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if request.url.path.startswith(AUTH_ROUTE_PREFIX):
        body = await request.body()
        logger.warning(
            "Auth request validation failed: "
            f"method={request.method} "
            f"path={request.url.path} "
            f"errors={errors} "
            f"body={_sanitize_request_body_for_logs(body)}"
        )
    else:
        logger.warning(
            "Request validation failed: "
            f"method={request.method} "
            f"path={request.url.path} "
            f"errors={errors}"
        )

    return await request_validation_exception_handler(request, exc)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

project_root = Path(__file__).parent.parent.parent
user_dir = project_root / "data" / "user"

try:
    from src.services.setup import init_user_directories

    init_user_directories(project_root)
except Exception:
    if not user_dir.exists():
        user_dir.mkdir(parents=True)

app.mount("/api/outputs", StaticFiles(directory=str(user_dir)), name="outputs")

# Auth routers (unprotected entry points)
auth_router, register_router, users_router = get_auth_routers()
app.include_router(auth_router, prefix="/auth/jwt", tags=["auth"])
app.include_router(register_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])

# Active routers
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(notebook.router, prefix="/api/v1/notebook", tags=["notebook"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(agent_config.router, prefix="/api/v1/agent-config", tags=["agent-config"])
app.include_router(profile.router, prefix="/api/v1", tags=["profile"])


@app.get("/")
async def root():
    return {"message": "Welcome to EducAgent API"}


@app.get("/health")
async def health():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as exc:
        logger.warning(f"Health check DB probe failed: {exc}")
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "disconnected"})


if __name__ == "__main__":
    import sys

    import uvicorn

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.services.setup import get_backend_port

    backend_port = get_backend_port(project_root)

    venv_dir = project_root / "venv"
    data_dir = project_root / "data"
    reload_excludes = [
        str(d)
        for d in [
            venv_dir,
            project_root / ".venv",
            data_dir,
            project_root / "web" / "node_modules",
            project_root / "web" / ".next",
            project_root / ".git",
        ]
        if d.exists()
    ]

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=backend_port,
        reload=True,
        reload_excludes=reload_excludes,
    )
