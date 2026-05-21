"""
CSRF Protection · Pattern Double-Submit Cookie + Synchronizer Token

Tous les endpoints mutants (POST/PUT/PATCH/DELETE) requièrent :
- Cookie csrf_token (HttpOnly=False, lisible par le JS pour le poser en header)
- Header X-CSRF-Token (envoyé par le frontend, doit matcher le cookie)
- Signature itsdangerous pour prévenir la falsification

Exempté pour : /api/auth/login, /api/auth/register (avant qu'on ait un cookie)
"""
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from ..config import settings

CSRF_COOKIE = "sia_csrf"
CSRF_HEADER = "X-CSRF-Token"
CSRF_MAX_AGE = 3600 * 8  # 8 heures

_serializer = URLSafeTimedSerializer(settings.JWT_SECRET, salt="csrf-token-v1")

# Exemptions (auth-bootstrap routes : pas encore de cookie)
EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/api/auth/password-reset",
    "/api/auth/password-reset-confirm",
}

# Méthodes nécessitant CSRF
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def generate_csrf_token() -> str:
    """Génère un token signé temporel."""
    raw = secrets.token_urlsafe(32)
    return _serializer.dumps(raw)


def validate_csrf_token(token: str) -> bool:
    """Valide un token signé (signature + expiration)."""
    try:
        _serializer.loads(token, max_age=CSRF_MAX_AGE)
        return True
    except SignatureExpired:
        logger.debug("CSRF token expired")
        return False
    except BadSignature:
        logger.warning("CSRF token bad signature (potential attack)")
        return False
    except Exception as e:
        logger.warning(f"CSRF token validation error: {e}")
        return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware Double-Submit Cookie :
    - GET/HEAD/OPTIONS : pose le cookie csrf_token si absent
    - POST/PUT/PATCH/DELETE : vérifie cookie == header X-CSRF-Token
    """

    def __init__(self, app: ASGIApp, secure: bool = True):
        super().__init__(app)
        self.secure = secure  # Mettre False uniquement en dev local

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Vérification sur méthodes mutantes
        if method in UNSAFE_METHODS and path not in EXEMPT_PATHS and path.startswith("/api/"):
            cookie_token = request.cookies.get(CSRF_COOKIE)
            header_token = request.headers.get(CSRF_HEADER)

            if not cookie_token or not header_token:
                logger.warning(f"CSRF missing tokens · path={path} ip={request.client.host if request.client else '?'}")
                raise HTTPException(status_code=403, detail="CSRF token manquant")

            # Double-submit check
            if cookie_token != header_token:
                logger.warning(f"CSRF mismatch · path={path} ip={request.client.host if request.client else '?'}")
                raise HTTPException(status_code=403, detail="CSRF token invalide")

            # Signature + expiration check
            if not validate_csrf_token(cookie_token):
                raise HTTPException(status_code=403, detail="CSRF token expiré ou falsifié")

        response = await call_next(request)

        # Poser le cookie CSRF s'il manque (GET/HEAD principalement)
        if path.startswith("/api/") and not request.cookies.get(CSRF_COOKIE):
            token = generate_csrf_token()
            response.set_cookie(
                key=CSRF_COOKIE,
                value=token,
                max_age=CSRF_MAX_AGE,
                httponly=False,           # JS doit pouvoir le lire pour l'envoyer en header
                secure=self.secure,
                samesite="lax",            # Lax permet navigations cross-site bénignes
                path="/",
            )

        return response
