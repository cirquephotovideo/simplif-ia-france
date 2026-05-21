"""Authentification : register, login, refresh.

Security v2:
- Cookies HttpOnly/Secure/SameSite pour JWT (en plus du body pour compat existante)
- Brute-force tracker (alerte si 5+ fails/min/IP)
- hCaptcha sur register et password-reset
- Audit logs immutables
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from ..config import settings
from ..database import get_db
from ..models import User, UserRole, UserPlan, AuditLog
from ..schemas.auth import LoginIn, RegisterIn, TokenOut, RefreshIn
from ..schemas.user import UserOut
from ..core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_current_user,
)
from ..core.captcha import verify_hcaptcha
from ..core.observability import login_failure_tracker
from loguru import logger

router = APIRouter()


async def _audit(db: AsyncSession, *, action: str, user_id=None, email=None, ip=None, ua=None, success=True, payload=None):
    db.add(AuditLog(
        action=action, actor_id=user_id, actor_email=email,
        ip_address=ip, user_agent=ua, success=success,
        payload=payload or {},
    ))


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Pose les cookies sécurité v2.
    HttpOnly = pas accessible au JS (anti-XSS)
    Secure = HTTPS only
    SameSite = anti-CSRF
    """
    common = dict(
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE.lower(),
        path="/",
    )
    if settings.COOKIE_DOMAIN:
        common["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(
        key="sia_access",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **common,
    )
    response.set_cookie(
        key="sia_refresh",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        **common,
    )


def _clear_auth_cookies(response: Response):
    common = dict(path="/", secure=settings.COOKIE_SECURE, httponly=True, samesite=settings.COOKIE_SAMESITE.lower())
    response.delete_cookie("sia_access", **common)
    response.delete_cookie("sia_refresh", **common)


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: RegisterIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    x_captcha_token: Optional[str] = Header(None, alias="X-Captcha-Token"),
):
    # hCaptcha verify (skip si pas configuré)
    if settings.HCAPTCHA_SECRET:
        await verify_hcaptcha(x_captcha_token or "", request)

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.USER,
        plan=UserPlan.FREE,
    )
    db.add(user)
    await db.flush()
    await _audit(db, action="user.register", user_id=user.id, email=user.email,
                 ip=request.client.host if request.client else None,
                 ua=request.headers.get("user-agent"))
    return user


@router.post("/login", response_model=TokenOut)
async def login(
    data: LoginIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        # Brute force tracker → alerte si seuil atteint
        login_failure_tracker.record_failure(ip, email=data.email)
        await _audit(db, action="user.login", email=data.email, success=False,
                     ip=ip, ua=request.headers.get("user-agent"))
        # Réponse uniforme pour ne pas leak l'existence du compte
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    if not user.is_active:
        await _audit(db, action="user.login", email=data.email, success=False,
                     payload={"reason": "account_disabled"}, ip=ip)
        raise HTTPException(status_code=403, detail="Compte désactivé")

    user.last_login_at = datetime.utcnow()
    await _audit(db, action="user.login", user_id=user.id, email=user.email,
                 ip=ip, ua=request.headers.get("user-agent"))

    access = create_access_token(str(user.id), {"role": user.role.value})
    refresh = create_refresh_token(str(user.id))

    # Cookies sécurisés v2 (en plus du body pour compatibilité existant)
    _set_auth_cookies(response, access, refresh)

    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(
    request: Request,
    response: Response,
    data: Optional[RefreshIn] = None,
    db: AsyncSession = Depends(get_db),
):
    # Accepter refresh token soit en body, soit en cookie
    refresh_token = (data.refresh_token if data else None) or request.cookies.get("sia_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token manquant")

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token invalide")

    sub = payload.get("sub")
    new_access = create_access_token(sub)
    new_refresh = create_refresh_token(sub)
    _set_auth_cookies(response, new_access, new_refresh)

    return TokenOut(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(current: User = Depends(get_current_user)):
    return current


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _audit(db, action="user.logout", user_id=current.id, email=current.email)
    _clear_auth_cookies(response)
    # TODO prod: ajouter une blacklist Redis pour invalider le JWT (jti)
    return None


@router.get("/csrf-token", status_code=200)
async def get_csrf_token(request: Request):
    """
    Endpoint pour récupérer le CSRF token avant les mutations.
    Le cookie est posé automatiquement par le CSRFMiddleware.
    Le frontend lit le cookie 'sia_csrf' et l'envoie en header 'X-CSRF-Token'.
    """
    token = request.cookies.get("sia_csrf")
    return {"csrf_token": token, "header": "X-CSRF-Token"}
