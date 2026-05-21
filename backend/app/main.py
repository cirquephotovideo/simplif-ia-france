"""Point d'entrée FastAPI · Security v2."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
import sys
import time

from .config import settings
from .database import engine, Base, AsyncSessionLocal
from .api import auth, users, vault, demarches, cerfas, ai, tts, gouv, admin, mails, vault_requests, settings as settings_api, api_credentials
from .core.bootstrap import bootstrap_admin
from .core.csrf import CSRFMiddleware
from .core.observability import init_sentry, setup_structured_logging


# === Logger structuré (JSON en prod pour Loki) ===
setup_structured_logging()

# === Sentry monitoring ===
init_sentry()

# === Rate limiter ===
limiter = Limiter(key_func=get_remote_address)


# === Security headers middleware (defense in depth, en plus de nginx) ===
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Headers minimum si nginx ne les pose pas (proxy direct, dev local)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        # Cache control par défaut pour les API JSON
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate")
            response.headers.setdefault("Pragma", "no-cache")
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 {settings.APP_NAME} starting · env={settings.APP_ENV} · sentry={'on' if settings.SENTRY_DSN else 'off'} · csrf={'on' if settings.CSRF_ENABLED else 'off'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await bootstrap_admin(db)
    logger.info("✅ Backend prêt")
    yield
    logger.info("👋 Backend arrêté")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Plateforme de simplification administrative française assistée par IA.",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# === Middlewares (ordre important : dernier ajouté = premier exécuté) ===
# 1. Compression gzip (executé last avant réponse)
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 2. Security headers (defense in depth)
app.add_middleware(SecurityHeadersMiddleware)

# 3. CSRF protection (avant CORS pour rejeter avant CORS preflight)
if settings.CSRF_ENABLED:
    app.add_middleware(CSRFMiddleware, secure=settings.COOKIE_SECURE)

# 4. CORS (autorise le frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Captcha-Token", "X-Requested-With"],
    expose_headers=["X-CSRF-Token", "X-RateLimit-Remaining"],
)

# 5. Trusted Host (anti DNS rebinding) en prod
if settings.APP_ENV == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)


@app.middleware("http")
async def log_and_timing(request: Request, call_next):
    """Log structuré + timing pour Loki/Sentry."""
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    # Log enrichi (Loki-ready)
    logger.bind(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:120],
    ).info(f"{request.method} {request.url.path} → {response.status_code} ({duration_ms:.0f}ms)")

    # Header de timing pour debug
    response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Erreur non gérée : {exc}")
    # En prod, ne pas leak la stack trace
    if settings.APP_ENV == "production":
        return JSONResponse(status_code=500, content={"detail": "Erreur interne"})
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": type(exc).__name__})


# === Routes ===
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Utilisateurs"])
app.include_router(vault.router, prefix="/api/vault", tags=["Coffre-fort"])
app.include_router(demarches.router, prefix="/api/demarches", tags=["Démarches"])
app.include_router(cerfas.router, prefix="/api/cerfas", tags=["CERFAs"])
app.include_router(ai.router, prefix="/api/ai", tags=["IA juridique"])
app.include_router(tts.router, prefix="/api/tts", tags=["Synthèse vocale"])
app.include_router(gouv.router, prefix="/api/gouv", tags=["APIs Gouv.fr"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(mails.router, prefix="/api/mails", tags=["Mails"])
app.include_router(vault_requests.router, prefix="/api/vault-requests", tags=["Demandes coffre"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["Settings admin"])
app.include_router(api_credentials.router, prefix="/api/credentials", tags=["Clés API"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs" if settings.DEBUG else "disabled in prod",
        "security": {
            "csrf_enabled": settings.CSRF_ENABLED,
            "captcha_enabled": bool(settings.HCAPTCHA_SECRET),
            "monitoring": "sentry" if settings.SENTRY_DSN else "logs only",
        },
    }
